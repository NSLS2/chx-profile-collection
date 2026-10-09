from typing import Annotated as A, Sequence, get_args, get_type_hints

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
)

from ophyd_async.epics.core import PvSuffix, EpicsDevice
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


class Orientation(StrictEnum):
    UP = "UP"
    RIGHT = "RIGHT"
    DOWN = "DOWN"
    LEFT = "LEFT"
    UP_MIRRORED = "UP_MIRRORED"
    RIGHT_MIRRORED = "RIGHT_MIRRORED"
    DOWN_MIRRORED = "DOWN_MIRRORED"
    LEFT_MIRRORED = "LEFT_MIRRORED"


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
    ikrum: A[SignalRW[int], PvSuffix("Ikrum_RBV"), Format.CONFIG_SIGNAL]
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
    global_timestamp_intvl: A[SignalRW[float], PvSuffix.rbv("GlblTimestampIntvl"), Format.CONFIG_SIGNAL]
    ref_clock: A[SignalRW[bool], PvSuffix.rbv("RefClock"), Format.CONFIG_SIGNAL]
    # log_level: A[SignalRW[int], PvSuffix.rbv("LogLevel"), Format.CONFIG_SIGNAL]
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
    bpc_write_file: A[SignalRW[bool], PvSuffix("WriteBPCFile")]

    dacs_filepath: A[SignalRW[str], PvSuffix.rbv("DACSFilePath"), Format.CONFIG_SIGNAL]
    dacs_filename: A[SignalRW[str], PvSuffix.rbv("DACSFileName"), Format.CONFIG_SIGNAL]
    dacs_filepath_exists: A[SignalR[bool], PvSuffix("DACSFilePathExists_RBV"), Format.CONFIG_SIGNAL]
    dacs_write_file: A[SignalRW[bool], PvSuffix("WriteDACSFile")]

    write_file_msg: A[SignalR[str], PvSuffix("WriteFileMessage")]

    # Filepath logic
    set_settings: A[SignalW[bool], PvSuffix("WriteData")]

    raw_filepath: A[SignalRW[str], PvSuffix.rbv("RawFilePath"), Format.CONFIG_SIGNAL]
    raw_file_template: A[SignalRW[str], PvSuffix.rbv("RawFileTemplate"), Format.CONFIG_SIGNAL]
    raw_write_enable: A[SignalRW[bool], PvSuffix.rbv("WriteRaw")]

    img_filepath: A[SignalRW[str], PvSuffix.rbv("ImgFilePath"), Format.CONFIG_SIGNAL]
    img_file_template: A[SignalRW[str], PvSuffix.rbv("ImgFileTemplate"), Format.CONFIG_SIGNAL]
    img_write_enable: A[SignalRW[bool], PvSuffix.rbv("WriteImg")]

    prv_filepath: A[SignalRW[str], PvSuffix.rbv("PrvImgFilePath"), Format.CONFIG_SIGNAL]
    prv_file_template: A[SignalRW[str], PvSuffix.rbv("PrvImgFileTemplate"), Format.CONFIG_SIGNAL]

    prv1_filepath: A[SignalRW[str], PvSuffix.rbv("PrvImg1FilePath"), Format.CONFIG_SIGNAL]

    async def init_file_writing(self) -> None:
        """Initialize filepaths on Serval through IOC and create directory on NFS"""
        self._write_path = str(self._path_provider(self._det_name).directory_path)

        # create directory in NFS
        await self.parent.hdf1.create_directory.set(-4)
        await self.parent.hdf1.file_path.set(self._write_path)


        # set directory/filename in Serval
        self._res_uid = str('-'.join(self._uu().split("-")[:-1]))
        await self.raw_filepath.set("file:" + self._write_path)
        # await self.raw_file_template.set(f"{self._res_uid}_0") # TODO i don't think we need this, gets called in trigger

        await self.raw_write_enable.set(True)
        await self.set_settings.set(True)

        # await self.update_file_template() # TODO shouldn't need this, it gets called on trigger
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
        name: str = "",
        *args,
        **kwargs
    ):
        assets_name = kwargs.pop("assets_name", "timepix")
        driver = Tpx3DriverIO(prefix + driver_suffix, path_provider, assets_name)
        _acquire_logic = Tpx3AcquireLogic(driver)

        plugins: dict[str, NDPluginBaseIO] = {
            "stats1": NDStatsIO(prefix=prefix + 'Stats1:', name="stats1"),
            "stats2": NDStatsIO(prefix=prefix + 'Stats2:', name="stats2"),
            "stats3": NDStatsIO(prefix=prefix + 'Stats3:', name="stats3"),
            "stats4": NDStatsIO(prefix=prefix + 'Stats4:', name="stats4"),
            "roi1": NDROIIO(prefix=prefix + 'ROI1:', name="roi1"),
            "roi2": NDROIIO(prefix=prefix + 'ROI2:', name="roi2"),
            "roi3": NDROIIO(prefix=prefix + 'ROI3:', name="roi3"),
            "roi4": NDROIIO(prefix=prefix + 'ROI4:', name="roi4"),
            "hdf1": NDPluginFileIO(prefix=prefix + 'HDF1:', name="hdf1")
        }

        super().__init__(
            prefix=prefix,
            driver=driver,
            name=name,
            plugins=plugins,
            acquire_logic=_acquire_logic,
            *args,
            **kwargs
        )

        # rename the raw_filepaths signal to match ophyd sync
        self.driver.raw_filepaths.set_name("files_raw_filepaths")

        # gather and add all config signals
        self.add_config_signals(*gather_config_signals(self))

        # register plugin signals
        for j in range(1, 5):
            stat = getattr(self, f"stats{j}")
            self.add_detector_logics(
                PluginSignalDataLogic(
                    driver=self.driver,
                    signal=stat.total,
                    hinted=True
                )
            )

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


pp = NSLS2PathProvider(RE.md)

with init_devices(child_name_separator="_"):
    tpx3_1 = Tpx3Detector("XF:11ID1-ES{TPX:1}", path_provider=pp, assets_name="timepix-1")

tpx3_1.driver.raw_filepaths.set_name(f"{tpx3_1.name}_files_raw_filepaths") 