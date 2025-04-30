

def energy_two_theta_scan(energies):

    starting_energy = dcm.en.user_readback.value
    starting_ivu_gap = ivu_gap.gap.user_readback.value
    starting_gam = diff.gam.user_readback.value
    starting_om = diff.om.user_readback.value

    for i, energy in enumerate(energies):

        print(f"Moving to {energy} keV: run {i+1}/{len(energies)}")

        move_E(energy, harm = 7)
        det = [elm]
        RE(dscan(det, ivu_gap, -40, 40, 50))
        ps()
        RE(mv(ivu_gap, ps.peak))
        det = [eiger1m_single]
        #RE(dscan(det, diff.gam, -0.2, 0.2, 40))
        #ps()
        #RE(mv(diff.gam, ps.cen))
        RE(dscan(det, diff.om, -0.2, 0.2, 40))
        ps()
        RE(mv(diff.om, ps.peak))

    move_E(starting_energy/1000, harm = 7)
    det = [elm]
    RE(dscan(det, ivu_gap, -40, 40, 50))
    ps()
    RE(mv(ivu_gap, ps.peak))
    RE(mv(diff.om, starting_om))
    RE(mv(diff.gam, starting_gam))


^Itime.sleep(600)
      ...: ^Iseries(det='eiger1m',expt=1,imnum=2000,feedback_on=True, auto_compression=True,comment='AUTO_COMMENT')
      ...: ^Iseries(det='eiger1m',expt=0.01,imnum=4500,feedback_on=True, auto_compression=True,comment='AUTO_COMMENT')

