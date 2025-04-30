def XPCSseries(expt,imnum,analysis='iso',position=True,OAV_mode="none"):
    if position:
        positions = " xh=%s yh=%s "%(round(diff.xh.user_readback.value,2),round(diff.yh.user_readback.value,2))
    else:
        positions=""    
    comment = 'AUTO_COMMENT'+positions

    RE.md["sample_x"]= round(diff.xh.user_readback.value,3)
    RE.md["sample_y"]= round(diff.yh.user_readback.value,3)
    series(det='eiger4m',expt=expt, imnum=imnum, feedback_on=True, analysis=analysis,auto_compression=True,comment=comment,OAV_mode=OAV_mode)
    RE.md.pop("sample_x")
    RE.md.pop("sample_y")
