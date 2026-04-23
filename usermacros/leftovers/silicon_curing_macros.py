# # Edges of sample holder: x_start: -5, x_end: 3, height1: 

def initialize_posdict():
    posdict={
        'slot1':{'md':{'sample':'0.17% DOTL','fill_time':1761855256.440267},
        'positions':{
        '1':{'y_start':-3.5,'h':-3.5,'x_start':-5.0,'y':-3.5,'x':-5.0},
        '2':{'y_start':-3.0,'h':-3.0,'x_start':-5.0,'y':-3.0,'x':-5.0},
        '3':{'y_start':-2.5,'h':-2.5,'x_start':-5.0,'y':-2.5,'x':-5.0},
        }
        },
        'slot2':{'md':{'sample':'0.17% DOTL','fill_time':1761855837.4772515},
        'positions':{
        '1':{'y_start':3,'h':3,'x_start':-5.5,'y':3,'x':-5.5},
        '2':{'y_start':3.5,'h':3.5,'x_start':-5.5,'y':3.5,'x':-5.5},
        '3':{'y_start':4,'h':4,'x_start':-5.5,'y':4,'x':-5.5},
        }
        },
        'slot3':{'md':{'sample':'DOTL 0.17 organic','fill_time':1761918997.9949675}, ## has the same position as slot 1, as it replaces slot 1 when we switch to new sample
        'positions':{
        '1':{'y_start':-9.9,'h':-10.2,'x_start':-5.5,'y':-9.9,'x':-5.5},
        '2':{'y_start':-9.3,'h':-9.6,'x_start':-5.5,'y':-9.3,'x':-5.5},
        '3':{'y_start':-8.7,'h':-9.,'x_start':-5.5,'y':-8.7,'x':-5.5},
        }
        }, 
    }
    return posdict


def reset_posdict(posdict,slot):
    for i in list(posdict[slot]['positions'].keys()):
        posdict[slot]['positions'][i]['y']=posdict[slot]['positions'][i]['y_start']
        posdict[slot]['positions'][i]['x']=posdict[slot]['positions'][i]['x_start']

def posdict_nextpos(posdict,slot,height,stepsize=.08):
    cur_y=posdict[slot]['positions'][height]['y']
    cur_x=posdict[slot]['positions'][height]['x']
    if cur_x+stepsize < posdict[slot]['positions'][height]['x_start']+3.2:
        posdict[slot]['positions'][height]['x']=cur_x+stepsize
    else:
        posdict[slot]['positions'][height]['x']=posdict[slot]['positions'][height]['x_start']
        posdict[slot]['positions'][height]['y']=cur_y+stepsize
    return posdict

def goto_posdict(posdict,slot,height):
    #if np.abs(diff.xh.user_readback.value) > .05:
    #    RE(mv(diff.xh,0))
    RE(mv(diff.yh,posdict[slot]['positions'][height]['y']))
    RE(mv(diff.xh,posdict[slot]['positions'][height]['x']))


def initial_sampling(slot): ## this covers the first ~120 minutes of curing
    att2.set_T(.0013/5)
    RE.md['sample']=RE.md['posdict'][slot]['md']['sample']
    RE.md['fill_time']=RE.md['posdict'][slot]['md']['fill_time']
    for i in range(1):
        for h in ['1','2','3']:
            RE.md['height no']=h;RE.md['height mm']=RE.md['posdict'][slot]['positions'][h]['y_start']
            # RE.md['rel humidity [perc]']=read_rh(temperature='auto')
            print('loop: %s   height: %s'%(i,h))

            ## Fastest scan
            goto_posdict(RE.md['posdict'],slot,h)
            series(det='eiger4m',expt=0.5,imnum=200, feedback_on=True,auto_compression=True,analysis='phi_4x_20deg',OAV_mode='none',comment='AUTO_COMMENT')
            temp_posdict=posdict_nextpos(RE.md['posdict'],slot,h,stepsize=.08);RE.md['posdict']=temp_posdict

            ## Faster scan
            goto_posdict(RE.md['posdict'],slot,h)
            series(det='eiger4m',expt=1,imnum=200, feedback_on=True,auto_compression=True,analysis='phi_4x_20deg',OAV_mode='none',comment='AUTO_COMMENT')
            temp_posdict=posdict_nextpos(RE.md['posdict'],slot,h,stepsize=.08);RE.md['posdict']=temp_posdict

            ## Slower scan
            goto_posdict(RE.md['posdict'],slot,h)
            series(det='eiger4m',expt=2,imnum=200, feedback_on=True,auto_compression=True,analysis='phi_4x_20deg',OAV_mode='none',comment='AUTO_COMMENT')
            temp_posdict=posdict_nextpos(RE.md['posdict'],slot,h,stepsize=.08);RE.md['posdict']=temp_posdict



def regular_sampling(slot): ## this covers ~60 minutes to ~120 minutes of curing
    att2.set_T(.0013/5)
    RE.md['sample']=RE.md['posdict'][slot]['md']['sample']
    RE.md['fill_time']=RE.md['posdict'][slot]['md']['fill_time']
    for i in range(1):
        for h in ['1','2','3']:
            RE.md['height no']=h;RE.md['height mm']=RE.md['posdict'][slot]['positions'][h]['y_start']
            print('loop: %s   height: %s'%(i,h))
            ## Faster scan
            goto_posdict(RE.md['posdict'],slot,h)
            series(det='eiger4m',expt=2,imnum=200, feedback_on=True,auto_compression=True,analysis='phi_4x_20deg',OAV_mode='none',comment='AUTO_COMMENT')
            temp_posdict=posdict_nextpos(RE.md['posdict'],slot,h,stepsize=.15);RE.md['posdict']=temp_posdict   
            ## Slower scan
            goto_posdict(RE.md['posdict'],slot,h)
            series(det='eiger4m',expt=5,imnum=200, feedback_on=True,auto_compression=True,analysis='phi_4x_20deg',OAV_mode='none',comment='AUTO_COMMENT')
            temp_posdict=posdict_nextpos(RE.md['posdict'],slot,h,stepsize=.15);RE.md['posdict']=temp_posdict        

def intermediate_sampling(slot): ## this covers ~120 minutes to ~1000 minutes
    att2.set_T(.0013/5)
    RE.md['sample']=RE.md['posdict'][slot]['md']['sample']
    RE.md['fill_time']=RE.md['posdict'][slot]['md']['fill_time']
    for i in range(1):
        for h in ['1','2','3']:
            RE.md['height no']=h;RE.md['height mm']=RE.md['posdict'][slot]['positions'][h]['y_start']
            # RE.md['rel humidity [perc]']=read_rh(temperature='auto')
            print('loop: %s   height: %s'%(i,h))
            goto_posdict(RE.md['posdict'],slot,h)
            series(det='eiger4m',expt=5,imnum=400, feedback_on=True,auto_compression=True,analysis='phi_4x_20deg',OAV_mode='none',comment='AUTO_COMMENT')
            temp_posdict=posdict_nextpos(RE.md['posdict'],slot,h,stepsize=.08);RE.md['posdict']=temp_posdict

def long_sampling(slot,height): ## to be used for t_age > 1000 minutes
    att2.set_T(.0013/5);att.set_T(.5)
    RE.md['sample']=RE.md['posdict'][slot]['md']['sample']
    RE.md['fill_time']=RE.md['posdict'][slot]['md']['fill_time']
    for i in range(1):
        for h in height:
            RE.md['height no']=h;RE.md['height mm']=RE.md['posdict'][slot]['positions'][h]['y_start']
            # RE.md['rel humidity [perc]']=read_rh(temperature='auto')
            print('loop: %s   height: %s'%(i,h))
            goto_posdict(RE.md['posdict'],slot,h)
            series(det='eiger4m',expt=5,imnum=720, feedback_on=True,auto_compression=True,analysis='phi_4x_20deg',OAV_mode='none',comment='AUTO_COMMENT')
            temp_posdict=posdict_nextpos(RE.md['posdict'],slot,h,stepsize=.08);RE.md['posdict']=temp_posdict



def overnight(slots): ## to be used after initial_curing_measurement(), for overnight scans
    ## slots must be list of strings: ['slot1','slot2']
    for i in range(2):
        for h in [['1'],['2'],['3']]:
            for s in slots:
                long_sampling(s,h)

def initial_curing_measurements(slots): ## this covers the full first 16 hours of curing (~1000 min). Does all heights in one slot before switching to the next slot
    ## slots must be list of strings: ['slot1','slot2']
    for i in range(4):
        for s in slots:
            initial_sampling(s)
    for j in range(4):
        for s in slots:
            regular_sampling(s)
    for k in range(10):
        for s in slots:
            intermediate_sampling(s)

def middle_curing_measurements(slots): ## this covers the full first 16 hours of curing (~1000 min). Does all heights in one slot before switching to the next slot
    ## slots must be list of strings: ['slot1','slot2']
    for j in range(3):
        for s in slots:
            regular_sampling(s)
    for k in range(10):
        for s in slots:
            intermediate_sampling(s)


# def overnight_test():
#     att2.set_T(.0013)
#     for i in range(20):
#         sam.x.move(-36.6+i*.1);RE.md['sample']='Silica Fusion 0.5% DOTL first test'
#         series(det='eiger4m',expt=5,imnum=200, feedback_on=True,auto_compression=True,OAV_mode='none',comment='AUTO_COMMENT')
#         sam.x.move(-22.3+i*.1);RE.md['sample']='Silica Fusion 0.05% DOTL first test'
#         series(det='eiger4m',expt=5,imnum=200, feedback_on=True,auto_compression=True,OAV_mode='none',comment='AUTO_COMMENT')
#         RE(sleep(1200))


# def finish_slot3(slot='slot3'):
#     att2.set_T(.0013/5)
#     RE.md['sample']=RE.md['posdict'][slot]['md']['sample']
#     RE.md['fill_time']=RE.md['posdict'][slot]['md']['fill_time']
#     for i in range(1):
#         for h in ['3','4','5']:
#             RE.md['height no']=h;RE.md['height mm']=RE.md['posdict'][slot]['positions'][h]['y_start']
#             print('loop: %s   height: %s'%(i,h))
#             goto_posdict(RE.md['posdict'],slot,h)
#             series(det='eiger4m',expt=5,imnum=200, feedback_on=True,auto_compression=True,OAV_mode='none',comment='AUTO_COMMENT')
#             temp_posdict=posdict_nextpos(RE.md['posdict'],slot,h,stepsize=.15);RE.md['posdict']=temp_posdict

# def post_sampling(sample_list):
#     #att2.set_T(.0013/5)
#     for sample in sample_list:
#         slot=sample[0];h=sample[1]
#         RE.md['sample']=RE.md['posdict'][slot]['md']['sample']
#         RE.md['fill_time']=RE.md['posdict'][slot]['md']['fill_time']
#         RE.md['height no']=h;RE.md['height mm']=RE.md['posdict'][slot]['positions'][h]['y_start']
#         print('measuring sample in %s height: %s'%(slot,h))
#         #goto_posdict(RE.md['posdict'],slot,h)
#         #att2.set_T(.0013/5)
#         #series(det='eiger4m',expt=2,imnum=200, feedback_on=True,auto_compression=True,OAV_mode='none',comment='AUTO_COMMENT')
#         #temp_posdict=posdict_nextpos(RE.md['posdict'],slot,h,stepsize=.15);RE.md['posdict']=temp_posdict
#         goto_posdict(RE.md['posdict'],slot,h)
#         att2.set_T(.0013/5)
#         series(det='eiger4m',expt=5,imnum=600, feedback_on=True,auto_compression=True,OAV_mode='none',comment='AUTO_COMMENT')
#         temp_posdict=posdict_nextpos(RE.md['posdict'],slot,h,stepsize=.08);RE.md['posdict']=temp_posdict


# def steps_2_3():
#     intial_sampling('slot2')
#     intermediate_sampling('slot1')

# def steps_4_to_10():
#     intial_sampling('slot3')
#     for s in ['slot2','slot1','slot3','slot2','slot1','slot3']:
#         intermediate_sampling(s)

# overnight_list=[['slot3','1'],['slot2','1'],['slot1','1'],['slot3','2'],['slot2','2'],['slot1','2'],
# ['slot3','3'],['slot2','3'],['slot1','3']]

# def clear_humidity_md():
#     RE.md['sample']='none'
#     md_list=['fill_time','height no','height mm','rel humidity [perc]']
#     for m in md_list:
#         RE.md.pop(m)

# def initial_measurements(reps=1):
#     slot_list=['slot2']
#     for r in range(reps):
#         for s in slot_list:
#             intial_sampling(s)
#         RE(sleep(600))

# def intermediate_measurements(reps=2):
#     slot_list=['slot2','slot1']
#     for r in range(reps):
#         for s in slot_list:
#             intermediate_sampling(s)
#         RE(sleep(300))

# def long_measurements(reps=1):
#     slot_list=['slot2','slot1']
#     att.set_T(.5)
#     for r in range(reps):
#         for s in slot_list:
#             long_sampling(s)
#         #RE(sleep(300))
#     att.set_T(1)

# def overnight_measurements():
#     #initial_measurements()
#     intermediate_measurements()
#     long_measurements()
#     intermediate_measurements()
#     long_measurements()
#     intermediate_measurements()

# def overnight_3D_printer():
#     # sample mounted to 3D printer for last measurements...manual mode!
#     RE.md['height mm']=-2
#     RE.md['rel humidity [perc]']='N.A.'
#     s1_x_start = [175.5,176.5]
#     s2_x_start = [199.5,200.5]
#     for r in range(2):
#         # slot1 measurements:
#         slot='slot1'
#         RE(mv(printer.x_bed,s1_x_start[r]))
#         # intermediate sampling 
#         att2.set_T(.0013/5)
#         RE.md['sample']=RE.md['posdict'][slot]['md']['sample']
#         RE.md['fill_time']=RE.md['posdict'][slot]['md']['fill_time']
#         series(det='eiger4m',expt=5,imnum=600, feedback_on=True,auto_compression=True,OAV_mode='none',comment='AUTO_COMMENT')
#         RE(mvr(printer.x_bed,.2))
#         # long intermediate
#         att.set_T(.5)
#         series(det='eiger4m',expt=10,imnum=720, feedback_on=True,auto_compression=True,OAV_mode='none',comment='AUTO_COMMENT')
#         att.set_T(1)

#         # slot2 measurements:
#         slot='slot2'
#         RE(mv(printer.x_bed,s2_x_start[r]))
#         # intermediate sampling
#         att2.set_T(.0013/5)
#         RE.md['sample']=RE.md['posdict'][slot]['md']['sample']
#         RE.md['fill_time']=RE.md['posdict'][slot]['md']['fill_time']
#         series(det='eiger4m',expt=5,imnum=600, feedback_on=True,auto_compression=True,OAV_mode='none',comment='AUTO_COMMENT')
#         RE(mvr(printer.x_bed,.2))
#         # long intermediate
#         att.set_T(.5)
#         series(det='eiger4m',expt=10,imnum=720, feedback_on=True,auto_compression=True,OAV_mode='none',comment='AUTO_COMMENT')
#         att.set_T(1)
