from typing import Annotated as A

from ophyd_async.core import (
    soft_signal_rw,
    SignalRW,
    SignalW,
    StandardReadable,
    StandardReadableFormat as Format,
)

from ophyd_async.epics.core import EpicsDevice, PvSuffix
from ophyd_async.epics.adcore import (
    AreaDetector,
    ADBaseIO,
    NDStatsIO,
    NDROIIO,
    NDPluginBaseIO,
)

class Tpx3DriverIO(ADBaseIO):
    ...


class Tpx3Files(StandardReadable, EpicsDevice):
    set_settings: A[SignalW[int], PvSuffix("WriteData")]

    raw_filepath: A[SignalRW[str], PvSuffix.rbv("RawFilePath"), Format.CONFIG_SIGNAL]
    raw_file_template: A[SignalRW[str], PvSuffix.rbv("RawFileTemplate"), Format.CONFIG_SIGNAL]
    raw_write_enable: A[SignalRW[int], PvSuffix.rbv("WriteRaw")]

    img_filepath: A[SignalRW[str], PvSuffix.rbv("ImgFilePath"), Format.CONFIG_SIGNAL]
    img_file_template: A[SignalRW[str], PvSuffix.rbv("ImgFileTemplate"), Format.CONFIG_SIGNAL]
    img_write_enable: A[SignalRW[int], PvSuffix.rbv("WriteImg")]

    prv_filepath: A[SignalRW[str], PvSuffix.rbv("PrvImgFilePath"), Format.CONFIG_SIGNAL]
    prv_file_template: A[SignalRW[str], PvSuffix.rbv("PrvImgFileTemplate"), Format.CONFIG_SIGNAL]

    prv1_filepath: A[SignalRW[str], PvSuffix.rbv("PrvImg1FilePath"), Format.CONFIG_SIGNAL]

    raw_filepaths = A[SignalRW[list], Format.UNCACHED_SIGNAL]




class Tpx3Detector(AreaDetector):

    def __init__(
        self,
        prefix: str,
        driver_suffix: str = "cam1:",
        name: str = "",
        *args,
        **kwargs
    ):

        driver = Tpx3DriverIO(prefix + driver_suffix)

        plugins: dict[str, NDPluginBaseIO] = {
            "stats1": NDStatsIO(prefix=prefix + 'Stats1:', name="stats1"),
            "stats2": NDStatsIO(prefix=prefix + 'Stats2:', name="stats2"),
            "stats3": NDStatsIO(prefix=prefix + 'Stats3:', name="stats3"),
            "stats4": NDStatsIO(prefix=prefix + 'Stats4:', name="stats4"),
            "roi1": NDROIIO(prefix=prefix + 'ROI1:', name="roi1"),
            "roi2": NDROIIO(prefix=prefix + 'ROI2:', name="roi2"),
            "roi3": NDROIIO(prefix=prefix + 'ROI3:', name="roi3"),
            "roi4": NDROIIO(prefix=prefix + 'ROI4:', name="roi4"),
        }

        super().__init__(
            prefix=prefix,
            driver=driver,
            name=name,
            plugins=plugins,
            *args,
            **kwargs
        )