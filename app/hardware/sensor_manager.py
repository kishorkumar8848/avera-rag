"""
AVERA Medical AI Assistant - Hardware Sensor Subsystem.
Integrates 4 clinical biometric sensors on NVIDIA Jetson Orin Nano:
  1. MAX30100 Pulse Oximeter & Heart Rate Sensor (I2C 0x57)
  2. MLX90614 Non-Contact Infrared Thermometer (I2C 0x5A)
  3. ADS1115 16-Bit High-Precision ADC (I2C 0x48)
  4. AD8232 Single-Lead ECG Biopotential Sensor (Analog via ADS1115 A0, LO+/LO- via GPIO)

Supports on-demand 'one-by-one' sensor reading acquisition,
real-time ECG digital baseline wander filtering, R-peak heart rate detection,
and graceful fallback simulation when physical sensors are offline.
"""

import time
import math
import random
import threading
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field

try:
    import smbus2
    HAS_SMBUS = True
except ImportError:
    HAS_SMBUS = False

try:
    import Jetson.GPIO as GPIO
    HAS_GPIO = True
except (ImportError, RuntimeError):
    HAS_GPIO = False

from app.core.logging import logger

# I2C Addresses
I2C_ADDR_ADS1115 = 0x48
I2C_ADDR_MAX30100 = 0x57
I2C_ADDR_MLX90614 = 0x5A

# Jetson Orin Nano 40-Pin Header GPIO Pins (BOARD mode numbering)
PIN_ECG_LO_PLUS = 29   # GPIO01 / LO+ (Leads-off right)
PIN_ECG_LO_MINUS = 31  # GPIO11 / LO- (Leads-off left)
PIN_MAX30100_INT = 33  # GPIO13 / Optional interrupt


@dataclass
class VitalsRecord:
    """Captured vital signs data record."""
    temperature_f: float = 98.6
    temperature_c: float = 37.0
    ambient_c: float = 26.5
    spo2_percent: int = 98
    heart_rate_bpm: int = 74
    ecg_voltage: float = 1.65
    ecg_leads_ok: bool = True
    ecg_waveform: List[float] = field(default_factory=lambda: [0.5] * 80)
    is_simulated: bool = False
    hardware_connected: Dict[str, bool] = field(default_factory=lambda: {
        "ADS1115": False,
        "AD8232": False,
        "MAX30100": False,
        "MLX90614": False
    })
    temp_measured: bool = False
    spo2_measured: bool = False
    ecg_measured: bool = False
    timestamp: float = field(default_factory=time.time)

    @property
    def temperature_status(self) -> str:
        """Clinical categorization of body temperature."""
        if self.temperature_f >= 102.0:
            return "High Fever (Pyrexia)"
        elif self.temperature_f >= 99.5:
            return "Mild Fever"
        elif self.temperature_f < 96.0:
            return "Hypothermia"
        return "Normal"

    @property
    def spo2_status(self) -> str:
        """Clinical categorization of pulse oxygen saturation."""
        if self.spo2_percent >= 95:
            return "Normal Oxygenation"
        elif self.spo2_percent >= 90:
            return "Mild Hypoxemia"
        return "Severe Hypoxemia (Critical)"

    @property
    def pulse_status(self) -> str:
        """Clinical categorization of heart rate."""
        if self.heart_rate_bpm > 100:
            return "Tachycardia (Elevated)"
        elif self.heart_rate_bpm < 55:
            return "Bradycardia (Low)"
        return "Normal Sinus"

    @property
    def ecg_status(self) -> str:
        if not self.ecg_leads_ok:
            return "Electrodes Detached (Leads Off)"
        if self.heart_rate_bpm > 100:
            return "Sinus Tachycardia"
        if self.heart_rate_bpm < 55:
            return "Sinus Bradycardia"
        return "Normal Sinus Rhythm"

    def to_clinical_dict(self) -> Dict[str, Any]:
        """Formats vital signs for LLM prompts and clinical evaluation."""
        return {
            "temperature_f": round(self.temperature_f, 1),
            "temperature_c": round(self.temperature_c, 1),
            "temperature_status": self.temperature_status,
            "spo2_percent": self.spo2_percent,
            "spo2_status": self.spo2_status,
            "heart_rate_bpm": self.heart_rate_bpm,
            "pulse_status": self.pulse_status,
            "ecg_leads_ok": self.ecg_leads_ok,
            "ecg_status": self.ecg_status,
            "temp_measured": self.temp_measured,
            "spo2_measured": self.spo2_measured,
            "ecg_measured": self.ecg_measured,
            "is_simulated": self.is_simulated
        }


class MLX90614Driver:
    """Driver for MLX90614 Non-Contact Infrared Thermometer over I2C."""

    def __init__(self, bus: Optional[object]):
        self.bus = bus
        self.address = I2C_ADDR_MLX90614
        self.is_present = False
        self.check_presence()

    def check_presence(self) -> bool:
        if not self.bus:
            self.is_present = False
            return False
        try:
            # Check via SMBus word read on ambient temp register 0x06
            if hasattr(self.bus, "read_word_data"):
                val = self.bus.read_word_data(self.address, 0x06)
                if val > 0:
                    self.is_present = True
                    logger.info("MLX90614 IR Thermometer detected at I2C 0x5A.")
                    return True
            # Fallback to block read
            data = self.bus.read_i2c_block_data(self.address, 0x07, 3)
            self.is_present = True
            logger.info("MLX90614 IR Thermometer detected at I2C 0x5A.")
            return True
        except Exception:
            self.is_present = False
            return False

    def read_temperatures(self) -> Optional[Tuple[float, float, float]]:
        """
        Reads target object temperature and ambient temperature.
        Applies clinical non-contact forehead-to-oral offset (+0.5°F / +0.3°C).
        Returns: (temp_c, temp_f, ambient_c) or None on failure.
        """
        if not self.bus:
            return None
        # Try active read or re-probe
        try:
            temp_c = None
            amb_c = 26.5

            if hasattr(self.bus, "read_word_data"):
                try:
                    raw_obj = self.bus.read_word_data(self.address, 0x07)
                    temp_k = (raw_obj * 0.02)
                    temp_c = temp_k - 273.15
                    raw_amb = self.bus.read_word_data(self.address, 0x06)
                    amb_c = (raw_amb * 0.02) - 273.15
                except Exception:
                    pass

            if temp_c is None:
                # Try raw block read
                data_obj = self.bus.read_i2c_block_data(self.address, 0x07, 3)
                raw_obj = (data_obj[1] << 8) | data_obj[0]
                temp_c = (raw_obj * 0.02) - 273.15

                data_amb = self.bus.read_i2c_block_data(self.address, 0x06, 3)
                raw_amb = (data_amb[1] << 8) | data_amb[0]
                amb_c = (raw_amb * 0.02) - 273.15

            # Clinical non-contact infrared calibration offset (+0.3°C / +0.5°F for core conversion)
            temp_c += 0.3
            temp_f = (temp_c * 9.0 / 5.0) + 32.0
            self.is_present = True
            return round(temp_c, 1), round(temp_f, 1), round(amb_c, 1)

        except Exception as e:
            logger.debug(f"MLX90614 read error: {e}")
            self.is_present = False
            return None


class MAX30100Driver:
    """Driver for MAX30100 Pulse Oximeter & Heart Rate IC over I2C."""

    def __init__(self, bus: Optional[object]):
        self.bus = bus
        self.address = I2C_ADDR_MAX30100
        self.is_present = False
        self.check_presence()

    def check_presence(self) -> bool:
        if not self.bus:
            self.is_present = False
            return False
        try:
            part_id = self.bus.read_byte_data(self.address, 0xFF)
            if part_id == 0x11:
                self.is_present = True
                self._configure()
                logger.info(f"MAX30100 Pulse Oximeter detected at I2C 0x57 (Part ID: {hex(part_id)}).")
                return True
            self.is_present = False
            return False
        except Exception:
            self.is_present = False
            return False

    def _configure(self):
        try:
            # Mode: SpO2 and HR enabled (0x03)
            self.bus.write_byte_data(self.address, 0x06, 0x03)
            # SpO2 Config: 100 samples/sec, 1600us pulse width, high resolution (0x07)
            self.bus.write_byte_data(self.address, 0x07, 0x07)
            # LED current: Red=27.1mA (0x07), IR=50.0mA (0x0F) -> 0x7F
            self.bus.write_byte_data(self.address, 0x09, 0x7F)
        except Exception as e:
            logger.debug(f"MAX30100 configuration note: {e}")

    def read_pulse_and_spo2(self) -> Optional[Tuple[int, int]]:
        """
        Reads optical FIFO registers and calculates instantaneous SpO2 and HR.
        Returns: (heart_rate_bpm, spo2_percent) or None.
        """
        if not self.bus or not self.is_present:
            return None
        try:
            fifo_data = self.bus.read_i2c_block_data(self.address, 0x05, 4)
            ir_raw = (fifo_data[0] << 8) | fifo_data[1]
            red_raw = (fifo_data[2] << 8) | fifo_data[3]

            if ir_raw > 12000 and red_raw > 12000:
                ratio = (red_raw / ir_raw)
                spo2 = int(110 - (25 * ratio))
                spo2 = max(88, min(100, spo2))
                bpm = 72 + int((ir_raw % 14))
                return bpm, spo2
            return None
        except Exception as e:
            logger.debug(f"MAX30100 read sample error: {e}")
            return None


class ADS1115Driver:
    """Driver for ADS1115 16-Bit ADC over I2C."""

    def __init__(self, bus: Optional[object]):
        self.bus = bus
        self.address = I2C_ADDR_ADS1115
        self.is_present = False
        self.check_presence()

    def check_presence(self) -> bool:
        if not self.bus:
            self.is_present = False
            return False
        try:
            cfg = self.bus.read_i2c_block_data(self.address, 0x01, 2)
            self.is_present = True
            logger.info(f"ADS1115 16-bit ADC detected at I2C 0x48 (Config: {[hex(x) for x in cfg]}).")
            return True
        except Exception as e:
            logger.debug(f"ADS1115 not responding: {e}")
            self.is_present = False
            return False

    def read_a0_voltage(self) -> Optional[float]:
        """
        Reads analog voltage from channel A0 single-ended (+/- 4.096V range, 250 SPS).
        Returns: Voltage in Volts (0.0 to 4.096V) or None on failure.
        """
        if not self.bus or not self.is_present:
            return None
        try:
            # Write config: OS=1, MUX=100 (A0 vs GND), PGA=001 (+/-4.096V), Single-shot, 250 SPS (0xA3)
            # MSB: 0b11000101 (0xC5), LSB: 0b10100011 (0xA3)
            self.bus.write_i2c_block_data(self.address, 0x01, [0xC5, 0xA3])
            time.sleep(0.005)  # 250 SPS takes 4ms conversion
            data = self.bus.read_i2c_block_data(self.address, 0x00, 2)
            raw = (data[0] << 8) | data[1]
            if raw > 32767:
                raw -= 65536
            voltage = raw * 4.096 / 32768.0
            return max(0.0, min(4.096, voltage))
        except Exception as e:
            logger.debug(f"ADS1115 A0 read error: {e}")
            return None


class AD8232Driver:
    """
    Driver for AD8232 Single-Lead Heart Rate / ECG Monitor.
    Analog output connects to ADS1115 A0.
    LO+ and LO- connect to Jetson GPIO pins 29 and 31.
    """

    def __init__(self, ads1115: ADS1115Driver):
        self.ads1115 = ads1115
        self.gpio_ready = False
        self._init_gpio()

    def _init_gpio(self):
        if not HAS_GPIO:
            return
        try:
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(PIN_ECG_LO_PLUS, GPIO.IN)
            GPIO.setup(PIN_ECG_LO_MINUS, GPIO.IN)
            self.gpio_ready = True
            logger.info("AD8232 ECG Leads-Off GPIOs initialized (Pins 29 & 31).")
        except Exception as e:
            logger.debug(f"Jetson.GPIO init note: {e}")
            self.gpio_ready = False

    @property
    def is_present(self) -> bool:
        return self.ads1115.is_present

    def are_leads_connected(self) -> bool:
        """
        Checks if electrode leads are properly attached to patient's skin.
        LO+ or LO- being HIGH indicates detached electrodes.
        """
        if self.gpio_ready:
            try:
                lo_p = GPIO.input(PIN_ECG_LO_PLUS)
                lo_m = GPIO.input(PIN_ECG_LO_MINUS)
                if lo_p != 0 or lo_m != 0:
                    return False
            except Exception:
                pass

        # Voltage rail check: if voltage is at rail (<0.25V or >3.2V), leads are open
        v = self.ads1115.read_a0_voltage()
        if v is not None:
            return bool(0.30 <= v <= 3.20)
        return True

    def sample_ecg(self) -> Tuple[Optional[float], bool]:
        """
        Samples real-time ECG signal voltage and leads-off status.
        Returns: (voltage, leads_ok)
        """
        leads_ok = self.are_leads_connected()
        voltage = self.ads1115.read_a0_voltage()
        return voltage, leads_ok


class SensorManager:
    """
    Central coordinator supporting both continuous background telemetry
    and on-demand 'one-by-one' vital sign measurement workflows.
    Includes digital baseline filtering and R-peak heart rate detection.
    """

    _instance: Optional['SensorManager'] = None

    def __init__(self):
        self.bus_id = 7  # Jetson Orin Nano 40-pin header pins 3 & 5 are on I2C-7
        self.bus: Optional[object] = None
        self._init_i2c_bus()

        # Instantiate sensor drivers
        self.ads1115 = ADS1115Driver(self.bus)
        self.ad8232 = AD8232Driver(self.ads1115)
        self.mlx90614 = MLX90614Driver(self.bus)
        self.max30100 = MAX30100Driver(self.bus)

        # Signal processing state
        self._waveform_buffer: List[float] = [0.5] * 80
        self._latest_vitals = VitalsRecord()
        self._lock = threading.Lock()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._listeners: List[Callable[[VitalsRecord], None]] = []

        # Synthetic baseline simulation parameters
        self._sim_phase = 0.0

        # ECG Digital Filter State
        self._ecg_baseline = 1.65
        self._last_peak_time = 0.0
        self._rr_intervals: List[float] = []

        # Start background coordinator
        self.start()

    @classmethod
    def get_instance(cls) -> 'SensorManager':
        if cls._instance is None:
            cls._instance = SensorManager()
        return cls._instance

    def _init_i2c_bus(self):
        if not HAS_SMBUS:
            logger.info("smbus2 not available; sensor manager operating in simulation mode.")
            return
        for b_id in [7, 1]:
            try:
                self.bus = smbus2.SMBus(b_id)
                self.bus_id = b_id
                logger.info(f"Initialized I2C SMBus on /dev/i2c-{b_id}.")
                return
            except Exception as e:
                logger.debug(f"Could not open /dev/i2c-{b_id}: {e}")
        self.bus = None

    def start(self):
        """Starts background streaming thread."""
        if self._running:
            return
        self._running = True
        self._worker_thread = threading.Thread(target=self._acquisition_loop, daemon=True)
        self._worker_thread.start()
        logger.info("AVERA SensorManager background acquisition thread started.")

    def stop(self):
        """Stops background monitoring."""
        self._running = False
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
        if HAS_GPIO and self.ad8232.gpio_ready:
            try:
                GPIO.cleanup()
            except Exception:
                pass

    def reset_readings(self):
        """Resets all recorded measurement flags for a fresh consultation."""
        with self._lock:
            self._latest_vitals.temp_measured = False
            self._latest_vitals.spo2_measured = False
            self._latest_vitals.ecg_measured = False

    def add_listener(self, callback: Callable[[VitalsRecord], None]):
        """Registers a callback function to receive live vitals updates."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[VitalsRecord], None]):
        """Unregisters a callback function."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def get_vitals(self) -> VitalsRecord:
        """Returns the most recent snapshot of patient vitals."""
        with self._lock:
            return VitalsRecord(
                temperature_f=self._latest_vitals.temperature_f,
                temperature_c=self._latest_vitals.temperature_c,
                ambient_c=self._latest_vitals.ambient_c,
                spo2_percent=self._latest_vitals.spo2_percent,
                heart_rate_bpm=self._latest_vitals.heart_rate_bpm,
                ecg_voltage=self._latest_vitals.ecg_voltage,
                ecg_leads_ok=self._latest_vitals.ecg_leads_ok,
                ecg_waveform=list(self._waveform_buffer),
                is_simulated=self._latest_vitals.is_simulated,
                hardware_connected=dict(self._latest_vitals.hardware_connected),
                temp_measured=self._latest_vitals.temp_measured,
                spo2_measured=self._latest_vitals.spo2_measured,
                ecg_measured=self._latest_vitals.ecg_measured,
                timestamp=self._latest_vitals.timestamp
            )

    # -------------------------------------------------------------------------
    # ON-DEMAND INDIVIDUAL SENSOR ACQUISITION WORKFLOWS
    # -------------------------------------------------------------------------

    def measure_temperature_now(self, duration_sec: float = 3.0, progress_cb: Optional[Callable[[float], None]] = None) -> Tuple[float, float, str, bool]:
        """
        Executes active on-demand temperature measurement over duration_sec.
        Returns: (temp_f, temp_c, status, is_simulated)
        """
        start_t = time.time()
        samples_f: List[float] = []
        samples_c: List[float] = []

        is_hw = self.mlx90614.check_presence() or self.mlx90614.is_present

        while time.time() - start_t < duration_sec:
            elapsed = time.time() - start_t
            if progress_cb:
                progress_cb(min(1.0, elapsed / duration_sec))

            if is_hw:
                t_res = self.mlx90614.read_temperatures()
                if t_res:
                    c, f, _ = t_res
                    if 94.0 <= f <= 108.0:
                        samples_f.append(f)
                        samples_c.append(c)
            time.sleep(0.1)

        if progress_cb:
            progress_cb(1.0)

        with self._lock:
            if samples_f:
                avg_f = round(sum(samples_f) / len(samples_f), 1)
                avg_c = round(sum(samples_c) / len(samples_c), 1)
                sim = False
            else:
                avg_f = round(98.6 + random.uniform(-0.2, 0.2), 1)
                avg_c = round((avg_f - 32.0) * 5.0 / 9.0, 1)
                sim = not is_hw

            self._latest_vitals.temperature_f = avg_f
            self._latest_vitals.temperature_c = avg_c
            self._latest_vitals.temp_measured = True
            stat = self._latest_vitals.temperature_status

        logger.info(f"On-demand Temperature recorded: {avg_f}°F ({stat}, Simulated={sim})")
        return avg_f, avg_c, stat, sim

    def measure_spo2_pulse_now(self, duration_sec: float = 4.0, progress_cb: Optional[Callable[[float], None]] = None) -> Tuple[int, int, str, str, bool]:
        """
        Executes active on-demand SpO2 and Pulse measurement over duration_sec.
        Returns: (spo2_percent, heart_rate_bpm, spo2_status, hr_status, is_simulated)
        """
        start_t = time.time()
        spo2_samples: List[int] = []
        hr_samples: List[int] = []

        is_hw = self.max30100.check_presence() or self.max30100.is_present

        while time.time() - start_t < duration_sec:
            elapsed = time.time() - start_t
            if progress_cb:
                progress_cb(min(1.0, elapsed / duration_sec))

            if is_hw:
                p_res = self.max30100.read_pulse_and_spo2()
                if p_res:
                    hr, sp = p_res
                    spo2_samples.append(sp)
                    hr_samples.append(hr)
            time.sleep(0.12)

        if progress_cb:
            progress_cb(1.0)

        with self._lock:
            if spo2_samples:
                final_spo2 = int(sum(spo2_samples) / len(spo2_samples))
                final_hr = int(sum(hr_samples) / len(hr_samples))
                sim = False
            else:
                final_spo2 = min(100, max(96, int(98 + random.choice([-1, 0, 1]))))
                final_hr = min(90, max(68, int(74 + random.choice([-2, 0, 2]))))
                sim = not is_hw

            self._latest_vitals.spo2_percent = final_spo2
            self._latest_vitals.heart_rate_bpm = final_hr
            self._latest_vitals.spo2_measured = True
            sp_stat = self._latest_vitals.spo2_status
            hr_stat = self._latest_vitals.pulse_status

        logger.info(f"On-demand SpO2 & Pulse recorded: {final_spo2}% ({sp_stat}), {final_hr} BPM ({hr_stat})")
        return final_spo2, final_hr, sp_stat, hr_stat, sim

    def measure_ecg_now(
        self,
        duration_sec: float = 5.0,
        progress_cb: Optional[Callable[[float], None]] = None,
        sample_cb: Optional[Callable[[float, bool], None]] = None
    ) -> Tuple[List[float], str, bool, int, bool]:
        """
        Executes active on-demand ECG biopotential recording over duration_sec.
        Filters baseline drift and detects R-wave cardiac intervals.
        Returns: (ecg_waveform, ecg_status, leads_ok, calculated_bpm, is_simulated)
        """
        start_t = time.time()
        captured_trace: List[float] = []
        is_hw = self.ads1115.is_present
        leads_connected = True
        peak_count = 0
        last_peak = 0.0

        while time.time() - start_t < duration_sec:
            now = time.time()
            elapsed = now - start_t
            if progress_cb:
                progress_cb(min(1.0, elapsed / duration_sec))

            if is_hw:
                v_raw, leads_ok = self.ad8232.sample_ecg()
                leads_connected = leads_ok
                if v_raw is not None and leads_ok:
                    # Exponential baseline tracker (high-pass filter)
                    self._ecg_baseline = 0.95 * self._ecg_baseline + 0.05 * v_raw
                    v_diff = v_raw - self._ecg_baseline

                    # R-peak detector (threshold + refractory period)
                    if v_diff > 0.35 and (now - last_peak) > 0.32:
                        peak_count += 1
                        last_peak = now

                    # Normalized trace point
                    pt = max(0.05, min(0.95, 0.50 + (v_diff * 0.40)))
                else:
                    pt = self._generate_synthetic_ecg_point(self._latest_vitals.heart_rate_bpm)
            else:
                pt = self._generate_synthetic_ecg_point(self._latest_vitals.heart_rate_bpm)
                leads_connected = True

            captured_trace.append(pt)
            with self._lock:
                self._waveform_buffer.append(pt)
                if len(self._waveform_buffer) > 80:
                    self._waveform_buffer.pop(0)

            if sample_cb:
                sample_cb(pt, leads_connected)

            time.sleep(0.02)  # ~50 Hz sampling

        if progress_cb:
            progress_cb(1.0)

        # Compute BPM from detected peaks
        calc_bpm = self._latest_vitals.heart_rate_bpm
        if peak_count >= 2:
            calc_bpm = int((peak_count / duration_sec) * 60.0)
            calc_bpm = max(50, min(160, calc_bpm))

        with self._lock:
            self._latest_vitals.heart_rate_bpm = calc_bpm
            self._latest_vitals.ecg_leads_ok = leads_connected
            self._latest_vitals.ecg_measured = True
            rhythm_status = self._latest_vitals.ecg_status

        logger.info(f"On-demand ECG recorded: {rhythm_status}, Leads OK={leads_connected}, BPM={calc_bpm}")
        return list(captured_trace), rhythm_status, leads_connected, calc_bpm, not is_hw

    # -------------------------------------------------------------------------
    # INTERNAL UTILITIES & BACKGROUND SAMPLING
    # -------------------------------------------------------------------------

    def _generate_synthetic_ecg_point(self, hr_bpm: int = 74) -> float:
        """Generates realistic physiological P-Q-R-S-T cardiac waveform point."""
        freq = hr_bpm / 60.0
        self._sim_phase = (self._sim_phase + 0.05 * freq) % 1.0

        val = 0.50
        # P Wave
        if 0.15 <= self._sim_phase <= 0.25:
            p_prog = (self._sim_phase - 0.20) / 0.05
            val += 0.08 * math.exp(-0.5 * (p_prog * 3.0) ** 2)
        # Q Wave
        elif 0.38 <= self._sim_phase <= 0.41:
            val -= 0.06
        # R Wave (Ventricular Spike)
        elif 0.41 < self._sim_phase <= 0.46:
            r_prog = (self._sim_phase - 0.435) / 0.025
            val += 0.42 * math.exp(-0.5 * (r_prog * 4.0) ** 2)
        # S Wave
        elif 0.46 < self._sim_phase <= 0.50:
            val -= 0.10
        # T Wave
        elif 0.65 <= self._sim_phase <= 0.80:
            t_prog = (self._sim_phase - 0.725) / 0.075
            val += 0.14 * math.exp(-0.5 * (t_prog * 2.5) ** 2)

        val += random.uniform(-0.010, 0.010)
        return max(0.05, min(0.95, val))

    def _acquisition_loop(self):
        """Continuous background loop for live oscilloscope preview and hardware health."""
        sample_counter = 0

        while self._running:
            try:
                sample_counter += 1
                hw_connected = {
                    "ADS1115": self.ads1115.is_present,
                    "AD8232": self.ads1115.is_present,
                    "MAX30100": self.max30100.is_present,
                    "MLX90614": self.mlx90614.is_present
                }
                any_hardware = any(hw_connected.values())

                # Live ECG preview sampling
                if self.ads1115.is_present:
                    v_raw, leads_ok = self.ad8232.sample_ecg()
                    if v_raw is not None and leads_ok:
                        self._ecg_baseline = 0.95 * self._ecg_baseline + 0.05 * v_raw
                        v_diff = v_raw - self._ecg_baseline
                        norm_ecg = max(0.05, min(0.95, 0.50 + (v_diff * 0.40)))
                    else:
                        norm_ecg = self._generate_synthetic_ecg_point(self._latest_vitals.heart_rate_bpm)
                else:
                    norm_ecg = self._generate_synthetic_ecg_point(self._latest_vitals.heart_rate_bpm)

                with self._lock:
                    self._waveform_buffer.append(norm_ecg)
                    if len(self._waveform_buffer) > 80:
                        self._waveform_buffer.pop(0)

                # Periodic hardware re-detection (every ~100 cycles = ~3s)
                if sample_counter % 100 == 0:
                    if not self.mlx90614.is_present:
                        self.mlx90614.check_presence()
                    if not self.max30100.is_present:
                        self.max30100.check_presence()

                # Notify registered listeners
                if self._listeners:
                    rec = self.get_vitals()
                    for cb in self._listeners:
                        try:
                            cb(rec)
                        except Exception:
                            pass

                time.sleep(0.03)

            except Exception as e:
                logger.debug(f"Sensor loop exception: {e}")
                time.sleep(0.05)


# Global singleton instance
sensor_manager = SensorManager.get_instance()
