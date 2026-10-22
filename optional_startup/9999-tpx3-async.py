from typing import Annotated as A, Sequence, get_args, get_type_hints
import dataclasses

from ophyd_async.core import (
    PathProvider,
    UUIDFilenameProvider,
    AsyncStatus,
    SignalRW,
    SignalR,
    SignalW,
    StandardReadable,
    Device,
    StandardReadableFormat as Format,
    StrictEnum,
    SoftSignalBackend,
    init_devices,
    NotConnectedError,
)

from ophyd_async.epics.core import PvSuffix, EpicsDevice, EpicsOptions
from ophyd_async.epics.adcore import (
    AreaDetector,
    ADBaseIO,
    ADAcquireLogic,
    NDStatsIO,
    NDROIIO,
    NDPluginBaseIO,
    NDPluginFileIO,
    PluginSignalDataLogic,
)
import numpy as np

from nslsii.ophyd_async.providers import NSLS2PathProvider


def gather_config_signals(device: Device) -> Sequence[SignalR]:
    config_signals: list[SignalR] = []
    annotations = get_type_hints(type(device), include_extras=True)

    for attr_name, child in device.children():
        annotation = annotations.get(attr_name)
        metadata = get_args(annotation)

        if isinstance(child, SignalR):
            if Format.CONFIG_SIGNAL in metadata:
                config_signals.append(child)
        else:
            config_signals.extend(gather_config_signals(child))

    return config_signals


class ChainMode(StrictEnum):
    NONE = "NONE"
    LEADER = "LEADER"
    FOLLOWER = "FOLLOWER"


class Polarity(StrictEnum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"


class TDC(StrictEnum):
    P0123 = "P0123"
    N0123 = "N0123"
    PNO123 = "PN0123"
    P0 = "P0"
    N0 = "N0"
    PN0 = "PN0"


class TriggerSelection(StrictEnum):
    ZERO = "0"
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"

class Orientation(StrictEnum):
    UP = "UP"
    RIGHT = "RIGHT"
    DOWN = "DOWN"
    LEFT = "LEFT"
    UP_MIRRORED = "UP_MIRRORED"
    RIGHT_MIRRORED = "RIGHT_MIRRORED"
    DOWN_MIRRORED = "DOWN_MIRRORED"
    LEFT_MIRRORED = "LEFT_MIRRORED"


class RawStream(StrictEnum):
    FILE = "file:/"
    HTTP = "http://"
    TCP = "tcp://"
    UNKNOWN = "unknown"


class SplitStrategy(StrictEnum):
    SINGLE_FILE = "single_file"
    FRAME = "frame"


class FilePathsSignal(SignalRW[Sequence[str]]):

    def __init__(self, name: str = ""):
        super().__init__(
            SoftSignalBackend(Sequence[str]),
            name=name,
        )

    async def describe(self):
        datakeys = await super().describe()
        ret_dict = await self.read()
        for val in ret_dict.values():
            if isinstance(val, dict) and 'value' in val:
                datakeys[self.name]["dtype_numpy"] = str(np.asarray(val['value']).dtype)

        return datakeys


class Tpx3AcquireLogic(ADAcquireLogic):

    def __init__(self, driver, *args, **kwargs):
        self.driver = driver
        super().__init__(driver, *args, **kwargs)

    async def start_acquiring(self):
        await self.driver.parent.driver.update_file_template()
        await super().start_acquiring()


class Tpx3ChipIO(EpicsDevice, StandardReadable):
    cp_pll: A[SignalR[int], PvSuffix("CP_PLL_RBV"), Format.CONFIG_SIGNAL]
    s1_off: A[SignalR[int], PvSuffix("S1_OFF_RBV"), Format.CONFIG_SIGNAL]
    s1_on: A[SignalR[int], PvSuffix("S1_ON_RBV"), Format.CONFIG_SIGNAL]
    s2_off: A[SignalR[int], PvSuffix("S2_OFF_RBV"), Format.CONFIG_SIGNAL]
    s2_on: A[SignalR[int], PvSuffix("S2_ON_RBV"), Format.CONFIG_SIGNAL]
    ikrum: A[SignalR[int], PvSuffix("Ikrum_RBV"), Format.CONFIG_SIGNAL]
    pixel_dac: A[SignalR[int], PvSuffix("PixelDAC_RBV"), Format.CONFIG_SIGNAL]
    preamp_off: A[SignalR[int], PvSuffix("Preamp_OFF_RBV"), Format.CONFIG_SIGNAL]
    preamp_on: A[SignalR[int], PvSuffix("Preamp_ON_RBV"), Format.CONFIG_SIGNAL]
    tp_buffer_in: A[SignalR[int], PvSuffix("TPbufferIn_RBV"), Format.CONFIG_SIGNAL]
    tp_buffer_out: A[SignalR[int], PvSuffix("TPbufferOut_RBV"), Format.CONFIG_SIGNAL]
    pll_vcntrl: A[SignalR[int], PvSuffix("PLL_Vcntrl_RBV"), Format.CONFIG_SIGNAL]
    v_preamp_ncas: A[SignalR[int], PvSuffix("VPreamp_NCAS_RBV"), Format.CONFIG_SIGNAL]
    vtp_coarse: A[SignalR[int], PvSuffix("VTP_coarse_RBV"), Format.CONFIG_SIGNAL]
    vtp_fine: A[SignalR[int], PvSuffix("VTP_fine_RBV"), Format.CONFIG_SIGNAL]
    vfbk: A[SignalR[int], PvSuffix("Vfbk_RBV"), Format.CONFIG_SIGNAL]
    vth_coarse: A[SignalRW[int], PvSuffix.rbv("Vth_coarse"), Format.CONFIG_SIGNAL]
    vth_fine: A[SignalRW[int], PvSuffix.rbv("Vth_fine"), Format.CONFIG_SIGNAL]
    adjust: A[SignalR[int], PvSuffix("Adjust_RBV"), Format.CONFIG_SIGNAL]
    layout: A[SignalR[str], PvSuffix("Layout_RBV"), Format.CONFIG_SIGNAL]
    temp: A[SignalR[int], PvSuffix("Temp_RBV"), Format.CONFIG_SIGNAL]


class Tpx3DriverIO(ADBaseIO, StandardReadable):
    # Serval info
    serval_connected: A[SignalR[bool], PvSuffix("ServalConnected_RBV"), Format.CONFIG_SIGNAL]
    det_connected: A[SignalR[bool], PvSuffix("DetConnected_RBV"), Format.CONFIG_SIGNAL]
    free_space: A[SignalR[float], PvSuffix("FreeSpace_RBV"), Format.CONFIG_SIGNAL]
    disk_lim_reach: A[SignalR[bool], PvSuffix("DiskLimReach_RBV"), Format.CONFIG_SIGNAL]
    disk_low_limit: A[SignalR[int], PvSuffix("DiskLowLimit_RBV"), Format.CONFIG_SIGNAL]
    write_speed: A[SignalR[float], PvSuffix("WriteSpeed_RBV"), Format.CONFIG_SIGNAL]

    # calcouts
    filewriter_calc1: A[SignalR[float], PvSuffix("FileWriterCalc1"), Format.CONFIG_SIGNAL]
    filewriter_calc2: A[SignalR[float], PvSuffix("FileWriterCalc2"), Format.CONFIG_SIGNAL]
    filewriter_calc: A[SignalR[float], PvSuffix("FileWriterCalc"), Format.CONFIG_SIGNAL]
    hotpixel_calc: A[SignalR[float], PvSuffix("HotPixelCalc"), Format.CONFIG_SIGNAL]
    tdc_calc: A[SignalR[float], PvSuffix("TdcCalc"), Format.CONFIG_SIGNAL]
    pel_evt_calc: A[SignalR[float], PvSuffix("PelEvtCalc"), Format.CONFIG_SIGNAL]
    tpx3_status_calc: A[SignalR[float], PvSuffix("Tpx3StatusCalc"), Format.CONFIG_SIGNAL]
    alarm_enable: A[SignalRW[bool], PvSuffix("AlarmDisable"), Format.CONFIG_SIGNAL]
    alarm: A[SignalR[float], PvSuffix("Alarm"), Format.CONFIG_SIGNAL]

    # General detector info
    server_url: A[SignalR[str], PvSuffix("ServerURL_RBV"), Format.CONFIG_SIGNAL]
    det_type: A[SignalR[str], PvSuffix("DetType_RBV"), Format.CONFIG_SIGNAL]
    fw_ts: A[SignalR[str], PvSuffix("FwTS_RBV"), Format.CONFIG_SIGNAL]
    http_code: A[SignalR[int], PvSuffix("HttpCode_RBV"), Format.CONFIG_SIGNAL]
    iface: A[SignalR[str], PvSuffix("Iface_RBV"), Format.CONFIG_SIGNAL]
    sw_ver: A[SignalR[str], PvSuffix("SW_ver_RBV"), Format.CONFIG_SIGNAL]
    pix_count: A[SignalR[int], PvSuffix("PixCount_RBV"), Format.CONFIG_SIGNAL]
    row_len: A[SignalR[int], PvSuffix("RowLen_RBV"), Format.CONFIG_SIGNAL]
    nchips: A[SignalR[int], PvSuffix("NChips_RBV"), Format.CONFIG_SIGNAL]
    nrows: A[SignalR[int], PvSuffix("NRows_RBV"), Format.CONFIG_SIGNAL]
    mpx_type: A[SignalR[int], PvSuffix("MpxType_RBV"), Format.CONFIG_SIGNAL]
    bch_board_id: A[SignalR[str], PvSuffix("BChBoardId_RBV"), Format.CONFIG_SIGNAL]
    ip_addr: A[SignalR[str], PvSuffix("IpAddr_RBV"), Format.CONFIG_SIGNAL]
    chip1_md: A[SignalR[str], PvSuffix("Chip1_RBV"), Format.CONFIG_SIGNAL]
    chip2_md: A[SignalR[str], PvSuffix("Chip2_RBV"), Format.CONFIG_SIGNAL]
    chip3_md: A[SignalR[str], PvSuffix("Chip3_RBV"), Format.CONFIG_SIGNAL]
    chip4_md: A[SignalR[str], PvSuffix("Chip4_RBV"), Format.CONFIG_SIGNAL]
    acq_modes: A[SignalR[int], PvSuffix("AcqModes_RBV"), Format.CONFIG_SIGNAL]
    clock_read: A[SignalR[float], PvSuffix("ClockRead_RBV"), Format.CONFIG_SIGNAL]
    max_pulse_count: A[SignalR[int], PvSuffix("MaxPulseCnt_RBV"), Format.CONFIG_SIGNAL]
    max_pulse_height: A[SignalR[float], PvSuffix("MaxPulseHgt_RBV"), Format.CONFIG_SIGNAL]
    timer_max_val: A[SignalR[float], PvSuffix("TimerMaxVal_RBV"), Format.CONFIG_SIGNAL]
    timer_min_val: A[SignalR[float], PvSuffix("TimerMinVal_RBV"), Format.CONFIG_SIGNAL]
    timer_step: A[SignalR[float], PvSuffix("TimerStep_RBV"), Format.CONFIG_SIGNAL]
    clock_timepix: A[SignalR[float], PvSuffix("ClockTimepix_RBV"), Format.CONFIG_SIGNAL]

    # Detector health
    local_temp: A[SignalR[float], PvSuffix("LocalTemp_RBV"), Format.CONFIG_SIGNAL]
    fpga_temp: A[SignalR[float], PvSuffix("FPGATemp_RBV"), Format.CONFIG_SIGNAL]
    fan1_speed: A[SignalR[float], PvSuffix("Fan1Speed_RBV"), Format.CONFIG_SIGNAL]
    fan2_speed: A[SignalR[float], PvSuffix("Fan2Speed_RBV"), Format.CONFIG_SIGNAL]
    bias_voltage_h: A[SignalR[float], PvSuffix("BiasVoltage_RBV"), Format.CONFIG_SIGNAL]
    humidity: A[SignalR[int], PvSuffix("Humidity_RBV"), Format.CONFIG_SIGNAL]
    chip_temps: A[SignalR[str], PvSuffix("ChipTemps_RBV"), Format.CONFIG_SIGNAL]
    vdd: A[SignalR[str], PvSuffix("VDD_RBV"), Format.CONFIG_SIGNAL]
    avdd: A[SignalR[str], PvSuffix("AVDD_RBV"), Format.CONFIG_SIGNAL]

    # Detector config
    fan1_pwm: A[SignalR[int], PvSuffix("Fan1PWM_RBV"), Format.CONFIG_SIGNAL]
    fan2_pwm: A[SignalR[int], PvSuffix("Fan2PWM_RBV"), Format.CONFIG_SIGNAL]
    bias_voltage: A[SignalRW[int], PvSuffix.rbv("BiasVolt"), Format.CONFIG_SIGNAL]
    bias_enable: A[SignalRW[bool], PvSuffix.rbv("BiasEnbl"), Format.CONFIG_SIGNAL]
    chain_mode: A[SignalRW[ChainMode], PvSuffix.rbv("ChainMode"), Format.CONFIG_SIGNAL]
    trigger_in: A[SignalRW[TriggerSelection], PvSuffix.rbv("TriggerIn"), Format.CONFIG_SIGNAL]
    trigger_out: A[SignalRW[TriggerSelection], PvSuffix.rbv("TriggerOut"), Format.CONFIG_SIGNAL]
    polarity: A[SignalRW[Polarity], PvSuffix.rbv("Polarity"), Format.CONFIG_SIGNAL]
    trigger_modec: A[SignalR[str], PvSuffix("TriggerModeC_RBV"), Format.CONFIG_SIGNAL]
    exposure_time: A[SignalR[float], PvSuffix("ExposureTime_RBV"), Format.CONFIG_SIGNAL]
    trigger_period: A[SignalR[float], PvSuffix("TriggerPeriod_RBV"), Format.CONFIG_SIGNAL]
    nTriggers: A[SignalR[int], PvSuffix("nTriggers_RBV"), Format.CONFIG_SIGNAL]
    periph_clk80: A[SignalRW[bool], PvSuffix("PeriphClk80"), Format.CONFIG_SIGNAL]
    trigger_delay: A[SignalRW[float], PvSuffix("TriggerDelay"), Format.CONFIG_SIGNAL]
    tdc: A[SignalR[str], PvSuffix("Tdc_RBV"), Format.CONFIG_SIGNAL]
    tdc_port0: A[SignalRW[TDC], PvSuffix.rbv("Tdc0"), Format.CONFIG_SIGNAL]
    tdc_port1: A[SignalRW[TDC], PvSuffix.rbv("Tdc1"), Format.CONFIG_SIGNAL]
    global_ts_interval: A[SignalRW[float], PvSuffix.rbv("GlblTimestampIntvl"), Format.CONFIG_SIGNAL]
    ref_clock: A[SignalRW[bool], PvSuffix.rbv("RefClock"), Format.CONFIG_SIGNAL]
    log_level: A[SignalRW[str], PvSuffix.rbv("LogLevel"), Format.CONFIG_SIGNAL]
    det_orientation: A[SignalRW[Orientation], PvSuffix.rbv("DetOrient"), Format.CONFIG_SIGNAL]

    # Detector chip config
    chip0: A[Tpx3ChipIO, PvSuffix("CHIP0_")]
    chip1: A[Tpx3ChipIO, PvSuffix("CHIP1_")]
    chip2: A[Tpx3ChipIO, PvSuffix("CHIP2_")]
    chip3: A[Tpx3ChipIO, PvSuffix("CHIP3_")]

    # BPC/DACS file config
    bpc_filepath: A[SignalRW[str], PvSuffix.rbv("BPCFilePath"), Format.CONFIG_SIGNAL]
    bpc_filename: A[SignalRW[str], PvSuffix.rbv("BPCFileName"), Format.CONFIG_SIGNAL]
    bpc_filepath_exists: A[SignalR[bool], PvSuffix("BPCFilePathExists_RBV"), Format.CONFIG_SIGNAL]
    bpc_write_file: A[SignalRW[bool], PvSuffix("WriteBPCFile"), EpicsOptions(wait=False)]
    dacs_filepath: A[SignalRW[str], PvSuffix.rbv("DACSFilePath"), Format.CONFIG_SIGNAL]
    dacs_filename: A[SignalRW[str], PvSuffix.rbv("DACSFileName"), Format.CONFIG_SIGNAL]
    dacs_filepath_exists: A[SignalR[bool], PvSuffix("DACSFilePathExists_RBV"), Format.CONFIG_SIGNAL]
    dacs_write_file: A[SignalRW[bool], PvSuffix("WriteDACSFile"), EpicsOptions(wait=False)]
    write_file_msg: A[SignalR[str], PvSuffix("WriteFileMessage")]

    # Filepath logic
    set_settings: A[SignalW[bool], PvSuffix("WriteData")]
    raw_filepath: A[SignalRW[str], PvSuffix.rbv("RawFilePath"), Format.CONFIG_SIGNAL]
    raw_file_template: A[SignalRW[str], PvSuffix.rbv("RawFileTemplate"), Format.CONFIG_SIGNAL]
    raw_write_enable: A[SignalRW[bool], PvSuffix.rbv("WriteRaw")]
    raw_stream: A[SignalRW[RawStream], PvSuffix("RawStream"), Format.CONFIG_SIGNAL]
    raw_queue_size: A[SignalRW[int], PvSuffix.rbv("RawQueueSize"), Format.CONFIG_SIGNAL]
    raw_split_strat: A[SignalRW[SplitStrategy], PvSuffix.rbv("RawSplitStg"), Format.CONFIG_SIGNAL]
    raw1_filepath: A[SignalRW[str], PvSuffix.rbv("Raw1FilePath"), Format.CONFIG_SIGNAL]
    raw1_file_template: A[SignalRW[str], PvSuffix.rbv("Raw1FileTemplate"), Format.CONFIG_SIGNAL]
    raw1_write_enable: A[SignalRW[bool], PvSuffix.rbv("WriteRaw1")]
    raw1_stream: A[SignalRW[RawStream], PvSuffix("Raw1Stream"), Format.CONFIG_SIGNAL]
    raw1_queue_size: A[SignalRW[int], PvSuffix.rbv("Raw1QueueSize"), Format.CONFIG_SIGNAL]
    raw1_split_strat: A[SignalRW[SplitStrategy], PvSuffix.rbv("Raw1SplitStg"), Format.CONFIG_SIGNAL]
    img_filepath: A[SignalRW[str], PvSuffix.rbv("ImgFilePath"), Format.CONFIG_SIGNAL]
    img_file_template: A[SignalRW[str], PvSuffix.rbv("ImgFileTemplate"), Format.CONFIG_SIGNAL]
    img_write_enable: A[SignalRW[bool], PvSuffix.rbv("WriteImg")]
    img1_filepath: A[SignalRW[str], PvSuffix.rbv("Img1FilePath"), Format.CONFIG_SIGNAL]
    img1_file_template: A[SignalRW[str], PvSuffix.rbv("Img1FileTemplate"), Format.CONFIG_SIGNAL]
    img1_write_enable: A[SignalRW[bool], PvSuffix.rbv("WriteImg1")]
    prv_filepath: A[SignalRW[str], PvSuffix.rbv("PrvImgFilePath"), Format.CONFIG_SIGNAL]
    prv_file_template: A[SignalRW[str], PvSuffix.rbv("PrvImgFileTemplate"), Format.CONFIG_SIGNAL]
    prv_write_enable: A[SignalRW[bool], PvSuffix.rbv("WritePrvImg")]
    prv1_filepath: A[SignalRW[str], PvSuffix.rbv("PrvImg1FilePath"), Format.CONFIG_SIGNAL]
    prv1_file_template: A[SignalRW[str], PvSuffix.rbv("PrvImg1FileTemplate"), Format.CONFIG_SIGNAL]
    prv1_write_enable: A[SignalRW[bool], PvSuffix.rbv("WritePrvImg1")]

    # Measurements
    pel_evt_rate: A[SignalR[int], PvSuffix("PelEvtRate_RBV")]
    tdc1_evt_rate: A[SignalR[int], PvSuffix("Tdc1EvtRate_RBV")]
    tdc2_evt_rate: A[SignalR[int], PvSuffix("Tdc1EvtRate_RBV")]
    start_time: A[SignalR[int], PvSuffix("StartTime_RBV")]
    elapsed_time: A[SignalR[int], PvSuffix("ElapsedTime_RBV")]
    time_left: A[SignalR[int], PvSuffix("TimeLeft_RBV")]
    frame_count: A[SignalR[int], PvSuffix("FrameCnt_RBV")]
    dropped_frames: A[SignalR[int], PvSuffix("DroppedFrames_RBV")]
    status: A[SignalR[str], PvSuffix("Status_RBV")]

    async def init_file_writing(self) -> None:
        """Initialize filepaths on Serval through IOC and create directory on NFS"""
        self._write_path = str(self._path_provider(self._det_name).directory_path)

        # create directory in NFS
        await self.parent.hdf1.create_directory.set(-4)
        await self.parent.hdf1.file_path.set(self._write_path)


        # set directory/filename in Serval
        self._res_uid = str('-'.join(self._uu().split("-")[:-1]))
        await self.raw_filepath.set("file:" + self._write_path)
        await self.raw_write_enable.set(True)
        await self.set_settings.set(True)

        self._n = 0

    async def uninit_file_writing(self) -> None:
        """Uninitialize filepaths on Serval through IOC"""
        await self.raw_filepath.set('file:placeholder')
        await self.raw_file_template.set(f"template_placeholder")
        await self.raw_write_enable.set(False)
        await self.set_settings.set(True)

    async def update_file_template(self) -> None:
        # set file template on Serval, will be <uid>_<n>_<serval_counter>.tpx3
        await self.raw_file_template.set(f"{self._res_uid}_{self._n:05d}_")
        await self.set_settings.set(True)

        # predict what the future filepaths will be
        num_images = await self.num_images.get_value()
        filenames = [f'{"file:" + self._write_path}/{self._res_uid}_{self._n:05d}_{j:06d}.tpx3' for j in range(num_images)] # TODO pretty sure we can remove 'file:' here
        await self.raw_filepaths.set(filenames)

        self._n += 1

    def __init__(self, prefix: str, path_provider: PathProvider, det_name: str, *args, **kwargs):
        self._path_provider = path_provider
        self._det_name = det_name
        self._uu = UUIDFilenameProvider()
        # soft signal that stores the predicted filepaths when staged
        with self.add_children_as_readables(Format.UNCACHED_SIGNAL):
            self.raw_filepaths = FilePathsSignal()

        super().__init__(prefix, *args, **kwargs)
  
        self._n = 0


class Tpx3Detector(AreaDetector[Tpx3DriverIO]):

    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        driver_suffix: str = "cam1:",
        plugins: dict[str, NDPluginBaseIO] = {},
        name: str = "",
        *args,
        **kwargs
    ):
        assets_name = kwargs.pop("assets_name", "timepix")
        driver = Tpx3DriverIO(prefix + driver_suffix, path_provider, assets_name)
        _acquire_logic = Tpx3AcquireLogic(driver)

        super().__init__(
            prefix=prefix,
            driver=driver,
            name=name,
            plugins=plugins,
            acquire_logic=_acquire_logic,
            *args,
            **kwargs
        )

        # gather and add all config signals
        self.add_config_signals(*gather_config_signals(self))

        self.add_detector_logics(
            PluginSignalDataLogic(
                driver=self.driver,
                signal=self.driver.raw_filepaths,
                hinted=False,
            )
        )

    @AsyncStatus.wrap
    async def stage(self) -> None:
        await self.driver.init_file_writing()
        await super().stage()

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        await self.driver.uninit_file_writing()
        await super().unstage()

## CHX Specific Utilities ##

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MethodType
import json

from bluesky.run_engine import call_in_bluesky_event_loop

@dataclass(frozen=True)
class Tpx3Mode():
    bpc_filepath: str | Path
    bpc_filename: str | Path
    dacs_filepath: str | Path
    dacs_filename: str | Path
    bias_voltage: int = 100
    global_ts_interval: float = 0.1

class Tpx3Modes(Enum):
    IKRUM3 =  "IKRUM3"
    IKRUM10 = "IKRUM10"
    IKRUM20 = "IKRUM20"

async def set_mode(self: Tpx3Detector, mode_name: Tpx3Modes):
    if mode_name not in self.modes:
        print(f"{self.name} does not have mode {mode_name.value}")

    mode = self.modes[mode_name]
    # write bpc
    await self.driver.bpc_filepath.set(mode.bpc_filepath)
    await self.driver.bpc_filename.set(mode.bpc_filename)
    await self.driver.bpc_write_file.set(True)

    # write dacs
    await self.driver.dacs_filepath.set(mode.dacs_filepath)
    await self.driver.dacs_filename.set(mode.dacs_filename)
    await self.driver.dacs_write_file.set(True)

    # set configurations
    await self.driver.bias_voltage.set(mode.bias_voltage)
    await self.driver.bias_enable.set(True)
    await self.driver.global_ts_interval.set(mode.global_ts_interval)

    # set filewriter configs
    await self.driver.prv_filepath.set("http://localhost")
    await self.driver.prv_write_enable.set(True)
    await self.driver.raw_write_enable.set(False)
    await self.driver.raw1_write_enable.set(False)
    await self.driver.img_write_enable.set(False)
    await self.driver.img1_write_enable.set(False)
    await self.driver.set_settings.set(True)

# do this to avoid putting CHX specific code in the ophyd implementation
Tpx3Detector.set_mode = set_mode

# CHX Detector Setup
pp = NSLS2PathProvider(RE.md)

try:
    with init_devices(child_name_separator="_"):
        prefix = "XF:11ID1-ES{TPX:1}"
        tpx3_1 = Tpx3Detector(
            prefix,
            path_provider=pp,
            plugins= {
                "stats1": NDStatsIO(f'{prefix}Stats1:', name="stats1"),
                "stats2": NDStatsIO(f'{prefix}Stats2:', name="stats2"),
                "stats3": NDStatsIO(f'{prefix}Stats3:', name="stats3"),
                "stats4": NDStatsIO(f'{prefix}Stats4:', name="stats4"),
                "roi1": NDROIIO(f'{prefix}ROI1:', name="roi1"),
                "roi2": NDROIIO(f'{prefix}ROI2:', name="roi2"),
                "roi3": NDROIIO(f'{prefix}ROI3:', name="roi3"),
                "roi4": NDROIIO(f'{prefix}ROI4:', name="roi4"),
                "hdf1": NDPluginFileIO(f'{prefix}HDF1:', name="hdf1")
            },
            assets_name="timepix-1")
        
        for j in range(1, 5):
            stat = getattr(tpx3_1, f"stats{j}")
            tpx3_1.add_detector_logics(
                PluginSignalDataLogic(
                    driver=tpx3_1.driver,
                    signal=stat.total,
                    hinted=True
                )
            )

        prefix = "XF:11ID1-ES{TPX:2}"
        tpx3_2 = Tpx3Detector(
            prefix,
            path_provider=pp,
            plugins= {
                "stats1": NDStatsIO(f'{prefix}Stats1:', name="stats1"),
                "stats2": NDStatsIO(f'{prefix}Stats2:', name="stats2"),
                "stats3": NDStatsIO(f'{prefix}Stats3:', name="stats3"),
                "stats4": NDStatsIO(f'{prefix}Stats4:', name="stats4"),
                "roi1": NDROIIO(f'{prefix}ROI1:', name="roi1"),
                "roi2": NDROIIO(f'{prefix}ROI2:', name="roi2"),
                "roi3": NDROIIO(f'{prefix}ROI3:', name="roi3"),
                "roi4": NDROIIO(f'{prefix}ROI4:', name="roi4"),
                "hdf1": NDPluginFileIO(f'{prefix}HDF1:', name="hdf1")
            },
            assets_name="timepix-2")
        
        for j in range(1, 5):
            stat = getattr(tpx3_2, f"stats{j}")
            tpx3_2.add_detector_logics(
                PluginSignalDataLogic(
                    driver=tpx3_2.driver,
                    signal=stat.total,
                    hinted=True
                )
            )

except NotConnectedError as exc:
    failed = [
        name for name in ("tpx3_1", "tpx3_2") if name in exc.sub_errors
    ]

    print(f"Failed to connect: {', '.join(failed)}")

# for legacy scripts
if globals().get("tpx3_1"):
    tpx3_1.driver.raw_filepaths.set_name(f"{tpx3_1.name}_files_raw_filepaths")
if globals().get("tpx3_2"):
    tpx3_2.driver.raw_filepaths.set_name(f"{tpx3_2.name}_files_raw_filepaths")

# plug modes
tpx3_config_filepath = "/nsls2/data/chx/shared/CHX_Setup/timepix/"
tpx3_1_modes = {"IKRUM10": Tpx3Mode(**(json.loads(Path(f"{tpx3_config_filepath}/timepix-1/mode_ikrum10.json").read_text())))}
tpx3_2_modes = {
    "IKRUM3": Tpx3Mode(**(json.loads(Path(f"{tpx3_config_filepath}/timepix-2/mode_ikrum3.json").read_text()))),
    "IKRUM10": Tpx3Mode(**(json.loads(Path(f"{tpx3_config_filepath}/timepix-2/mode_ikrum10.json").read_text()))),
    "IKRUM20": Tpx3Mode(**(json.loads(Path(f"{tpx3_config_filepath}/timepix-2/mode_ikrum20.json").read_text()))),
}
setattr(tpx3_1, "modes", {Tpx3Modes.IKRUM10: tpx3_1_modes["IKRUM10"]})
setattr(tpx3_2, "modes", {Tpx3Modes.IKRUM10: tpx3_2_modes["IKRUM3, IKRUM10, IKRUM20"]})

# initialize with default mode (ikrum 10)
call_in_bluesky_event_loop(tpx3_1.set_mode(Tpx3Modes.IKRUM10))
call_in_bluesky_event_loop(tpx3_2.set_mode(Tpx3Modes.IKRUM10))