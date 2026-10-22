from opentrons import protocol_api

metadata = {
    "protocolName": "D9:Thermocycler Module加载",
    "author": "Your Name"
}#都是字典类型

requirements = {
    "robotType": "Flex",
    "apiLevel": "2.29"
}#都是字典类型


def run(protocol: protocol_api.ProtocolContext):

    # 1. Load labware
    tips_50 = protocol.load_labware("opentrons_flex_96_tiprack_50ul","C2")
    tips_200 = protocol.load_labware("opentrons_flex_96_tiprack_200ul","C3")

    #所有的模块的耗材必须符合模块的要求，详情见各模块的Supported labware
    plate_buffer = protocol.load_labware("axygen_96_wellplate_500ul","D1")
    #设置一个plate，用来混匀mix

    # 2. Load pipette
    right_pipette = protocol.load_instrument("flex_1channel_50","right",tip_racks=[tips_50]) 
    left_pipette = protocol.load_instrument("flex_1channel_1000","left",tip_racks=[tips_200])

    # 3. Load trash
    trash = protocol.load_trash_bin("A3")
    
    # 4. Load module
    #Use the load_labware() method on the module context to load labware on a module. 
    #Thermocycler的位置固定在B1
    tc_mod = protocol.load_module(
        module_name="thermocyclerModuleV2")
    tc_plate = tc_mod.load_labware( 
        name="opentrons_96_wellplate_200ul_pcr_full_skirt",
        label="Temperature-Controlled Tubes")#顾名思义，label这个参数可有可无
    
    # 5. Lid control
    #The Thermocycler can control the position and temperature of its lid.
    #Once the lid is open, pipettes are able to access the loaded labware.
    #You can also control the temperature of the lid. Acceptable target temperatures are between 37 and 110 °C. To set the lid temperature, choose between a blocking and concurrent command. Each takes one parameter: the target temperature (in degrees Celsius) as an integer.（所以不能是37.5这种奇怪的温度） 
    tc_mod.set_lid_temperature(temperature=50)
    #When you use a blocking method like set_lid_temperature(), your protocol will only proceed once the lid temperature reaches 50 °C. 等到温度到50度再启动下一步。（这下看懂了）
    tc_mod.start_set_lid_temperature(temperature=60)
    #Use the concurrent start_set_lid_temperature() method to allow your protocol to proceed while the lid heats. 不用等温度到50度，直接开始下一步
    tc_mod.deactivate_lid()
    #You can turn off the lid heater at any time.
    
    
    # 6. Block control
    # Temperature
    tc_mod.set_block_temperature(temperature=4)
    #When you use a blocking method like set_block_temperature(), your protocol will only proceed once the block temperature reaches 4 °C.
    tc_mod.start_set_block_temperature(temperature=4)
    #Use the concurrent start_set_block_temperature() method to perform other protocol steps while the block reaches its target temperature.
    #和lid一样，PCR的话肯定得到温度再开始下一步吧
    
    # Timing temperature holds
    tc_mod.open_lid()
    tc_mod.set_block_temperature(
        temperature=4,  #float. A value between 4 and 99, representing the target temperature in °C.
        hold_time_minutes=4,  #float 
        hold_time_seconds=15)  #float 
    right_pipette.pick_up_tip()
    right_pipette.aspirate(50, tc_plate["A1"])
    right_pipette.dispense(50, tc_plate["B1"])
    right_pipette.drop_tip()
    #When you use the blocking set_block_temperature() command, you can specify hold_time_minutes, hold_time_seconds, or both (in which case they will be added together). Here, the Temperature Module reaches the target temperature and the robot holds for 4 minutes and 15 seconds. Your protocol won't proceed to further commands until the target temperature is reached and the hold is completed. 
    cool_task = tc_mod.start_set_block_temperature(temperature=4) # set block temperature
    right_pipette.pick_up_tip() # complete pipetting actions while the block cools
    right_pipette.aspirate(50, tc_plate["A1"])
    right_pipette.dispense(50, tc_plate["B1"])
    right_pipette.drop_tip()
    protocol.wait_for_tasks([cool_task]) # wait for the block to reach the target temperature. 注意：wait_for_tasks(tasks: list[Task]) -> None  这是list，就是说可以执行好几个程序。
    block_timer = protocol.create_timer(seconds=255) # hold samples on the block at target temperature. 注意：create_timer(seconds: float) -> Task  好家伙，还有timer，而且这个timer是隶属于protocol的。可以可以。
    protocol.wait_for_tasks([block_timer])
    #The concurrent start_set_block_temperature() method doesn't accept hold time arguments. Instead, use create_timer() to proceed to the next steps in the protocol. Here, the robot will perform the pipetting actions while the block reaches its target temperature. Once the protocol reaches the wait_for_tasks() commands, the robot pauses and waits for the block to finish cooling or holds for the remainder of the timer.
    task_a=tc_mod.start_set_block_temperature(temperature=42)
    task_b=protocol.create_timer(seconds=90.5)
    task_c=tc_mod.start_set_block_temperature(temperature=4)
    task_d=protocol.create_timer(seconds=176.4)
    protocol.wait_for_tasks([task_a,task_b,task_c,task_d])
    #所以你看，这里也是隶属于protocol类下的，说明这是个底层方法。
    
    # Ramp rate
    tc_mod.set_block_temperature(
        temperature=4,  #也是set_block_temperature的参数之一
        ramp_rate=1)
    #Here, the Thermocycler Module will cool the block to 4 °C at a rate of 1 °C/second. 
    tc_mod.start_set_block_temperature(
        temperature=4,
        ramp_rate=1)
    # float. in °C/second. The acceptable range is 0.01–2 °C/second to cool the block, and 0.01–4.25 °C/second to heat the block. If not specified, the block will heat or cool as quickly as possible to reach the set temperature.
    
    # Block max volume
    tc_mod.set_block_temperature(
        temperature=4,
        hold_time_seconds=20,
        block_max_volume=80) 
    # float. in µL. If not specified, the default is 25 µL.
    
    
    # 7. Thermocycler profiles（重点来了）
    #These sequences are called profiles, which are defined in the Protocol API as lists of dictionaries（字典类型）. Each dictionary within the profile should have a temperature key, which specifies the temperature of the step, and either or both of hold_time_seconds and hold_time_minutes, which specify the duration of the step.
    #For example, this profile commands the Thermocycler to reach 10 °C and hold for 30 seconds, and then to reach 60 °C and hold for 45 seconds:
    profile = [
        {"temperature":10, "hold_time_seconds":30},
        {"temperature":60, "hold_time_seconds":45}
        ]
    #Once you have written the steps of your profile, choose a blocking or concurrent command to execute it with. Both execute your profile steps multiple times depending on the repetitions parameter. Each also takes a block_max_volume parameter, which is the same as that of the set_block_temperature() and start_set_block_temperature() functions.
    #For instance, a PCR prep protocol might define and execute a profile like this:
    profile = [
        {"temperature":95, "hold_time_seconds":30},
        {"temperature":57, "hold_time_seconds":30},
        {"temperature":72, "hold_time_seconds":60}
        ]
    tc_mod.execute_profile(
        steps=profile, 
        repetitions=20, 
        block_max_volume=32)
    #tc_mod.start_execute_profile(
    #    steps=profile, 
    #    repetitions=20,
    #    block_max_volume=32)
    #同上
    '''
    和这个是等价的
    for i in range(20):
        tc_mod.set_block_temperature(95, hold_time_seconds=30, block_max_volume=32)
        tc_mod.set_block_temperature(57, hold_time_seconds=30, block_max_volume=32)
        tc_mod.set_block_temperature(72, hold_time_seconds=60, block_max_volume=32)
    '''
    #那么，如果想梯度退火，即每个循环降1度该怎么设置呢？首先，必须用循环，因为profile是固定的；其次如同官网所述，每次用循环会产生大量日志。是否能结合？
    for i in range(20):
        profile = [
            {"temperature":95, "hold_time_seconds":30},
            {"temperature":62-i*0.5, "hold_time_seconds":30},
            {"temperature":72, "hold_time_seconds":30}]
        tc_mod.execute_profile(
            steps=profile, 
            repetitions=1,  #repetitions参数不可省
            block_max_volume=25)
        
    # 8. Auto-sealing lids（上一期的问题）
    #Starting in robot software version 8.2.0, you can use the Opentrons Tough PCR Auto-sealing Lid to reduce evaporation on the Thermocycler. 
    #They also work with the Opentrons Flex Deck Riser adapter, which keeps lids away from the unsterilized deck and provides better access for the gripper. 这玩意就看看就行。
    #You can load auto-sealing lids in a few ways:
        #Load a single auto-sealing lid onto a compatible location (the deck, the riser, or another lid) with the appropriate load_labware() method.
        #Use ProtocolContext.load_lid_stack() to create a stack of up to five auto-sealing lids directly on the deck. <=5
        #Use Labware.load_lid_stack() to create a stack of up to five auto-sealing lids on the riser. <=5
    #不管什么情况，>5个lid就会报错
    #如果不使用 Riser，直接将盖子放在甲板上，最多只能堆叠 3 个。而使用 Riser 后，可以堆叠多达 5 个盖子，能显著增加单次协议运行的耗材装载量。（来源于deepseek）
    # load riser
    riser = protocol.load_adapter(
        load_name="opentrons_flex_deck_riser", location="A2"
        )
    # load a stack of three lids
    lid_stack = riser.load_lid_stack(  #这里直接用riser.load_lid_stack，所以就直接load在riser上
        load_name="opentrons_tough_pcr_auto_sealing_lid",
        quantity=3
        )
    
    # move lid to PCR plate
    protocol.move_lid(
        source_location=lid_stack,
        new_location=tc_plate,
        use_gripper=True
        )
    # close Thermocycler
    tc_mod.close_lid()
        
    

    
    
    
    
    
    
    