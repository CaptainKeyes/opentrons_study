from opentrons import protocol_api

metadata = {
    "protocolName": "D11:Heater-Shaker Module加载",
    "author": "Your Name"
}#都是字典类型

requirements = {
    "robotType": "Flex",
    "apiLevel": "2.29"
}#都是字典类型


def run(protocol: protocol_api.ProtocolContext):
    # 1. Load labware
    tips_50 = protocol.load_labware("opentrons_flex_96_tiprack_50ul","C2")
    plate_PCR = protocol.load_labware("opentrons_96_wellplate_200ul_pcr_full_skirt","D2")#PCR的板子是特制板子
    plate_sample = protocol.load_labware("corning_96_wellplate_360ul_flat","D3")#设置一个plate，存放样品

    # 2. Load pipette
    pipette_50 = protocol.load_instrument(
        "flex_1channel_50","left",tip_racks=[tips_50])

    #见Tip-pipette compatibility

    # 3. Load trash
    trash = protocol.load_trash_bin("A3")
    
    # 4. Load Heater-Shaker module
    hs_mod = protocol.load_module(
        module_name="heaterShakerModuleV1", location="D1"
        )
    #In any deck slot in column 1 or 3. The module can go in slot A3, but you need to move the trash bin first.
    
    # 5. Latch control
    #To add and remove labware from the Heater-Shaker, control the module's labware latch from your protocol using open_labware_latch() and close_labware_latch(). 
    #Shaking requires the labware latch to be closed, so you may want to issue a close command before the first shake command in your protocol:
    hs_mod.close_labware_latch()
    hs_mod.set_and_wait_for_shake_speed(500)
    
    
    # 6. Loading labware
    #Use the Heater-Shaker’s load_adapter() and load_labware() methods to specify what you will place on the module. For the Heater-Shaker, use one of the thermal adapters listed below and labware that fits on the adapter. See Loading Labware on Adapters for examples.
    #和PCR仪不同，shaker是需要adaptor的
    #The Opentrons Labware Library includes definitions for both standalone adapters and adapter–labware combinations. These labware definitions help make the Heater-Shaker ready to use right out of the box.同样也是表中自己找
    #For example, these commands load a well plate on top of the flat bottom adapter，和PCR仪一样，也是直接load在shaker上:
    hs_adapter = hs_mod.load_adapter("opentrons_96_flat_bottom_adapter")
    hs_plate = hs_adapter.load_labware("nest_96_wellplate_200ul_flat")
    
    # 7. Heating and shaking
    #thermocycler一样，heatershaker也支持block和concurrent
    #Blocking commands: The robot will pause and wait, performing no other actions until the module reaches the required temperature or shake speed.包括：set_and_wait_for_temperature()，wait_for_temperature()，set_and_wait_for_shake_speed()。反正只要有“wait”就是
    #Concurrent commands: The robot continues to perform subsequent actions while heating or shaking. For example, continue pipetting, move labware, or run other modules. 包括：set_target_temperature()，set_shake_speed()。反正没有“wait”。
    
    # 8. Heating
    # Blocking
    #When you use a blocking command like set_and_wait_for_temperature(), your protocol proceeds completely linearly（线性执行，做完这个再做下一个）. No other commands will execute until the Heater-Shaker Module reaches the target temperature. In this example, the robot will perform the pipetting steps and protocol delay only after the module reaches 75 °C.
    hs_mod.set_and_wait_for_temperature(celsius=75)
    pipette_50.pick_up_tip()
    pipette_50.aspirate(50, plate_sample["A1"])
    #模块振荡期间，移液器不允许移动到 Heater-Shaker 所在槽位或其相邻槽位(防止碰撞和振动干扰)。由于默认heaterShaker的位置是D1(更何况你自己设置的就是D1)
    #PipetteMovementRestrictedByHeaterShakerError: Cannot movepipette to Heater-Shaker or adjacent slot while module isshaking
    pipette_50.dispense(50, plate_sample["B1"])
    pipette_50.drop_tip()
    protocol.delay(minutes=1)#让协议暂停 1 分钟，期间机械臂不做任何动作，但加热模块保持当前温度。常用于孵育、混匀后静置、或等待反应进行。
    #看到这里有set_and_wait就知道肯定是blocking方式
    # Concurrent
    #To perform other actions while the module reaches its target temperature, use the concurrent set_target_temperature() command. Here, the robot will continue to perform pipetting steps and a protocol delay while the Heater-Shaker heats to 75 °C.
    hs_mod.set_target_temperature(celsius=75)
    pipette_50.pick_up_tip()
    pipette_50.aspirate(50, plate_sample["A1"])
    pipette_50.dispense(50, plate_sample["B1"])
    pipette_50.drop_tip()
    protocol.delay(minutes=1)
    #这里就没有wait字样
    # Timer
    #If you want the robot to continue pipetting while the module heats to prepare for a sample incubation, you can use create_timer():
    # set target temperature
    heat_task = hs_mod.set_target_temperature(celsius=75)
    # pipette while the module heats
    pipette_50.pick_up_tip()
    pipette_50.aspirate(50, plate_sample["A1"])
    pipette_50.dispense(50, plate_sample["B1"])
    pipette_50.drop_tip()
    # wait for the module to finish heating
    protocol.wait_for_tasks([heat_task]) #区别wait_for_tasks和之前的dalay
    # set and hold for a sample incubation 
    incubation_timer = protocol.create_timer(seconds=120)
    protocol.wait_for_tasks([incubation_timer])
    hs_mod.deactivate_heater()
    #这个timer也是在设置PCR仪的时候用过，用来在PCR仪中进行保温。
    #Here, the robot will perform protocol steps placed after the concurrent set_target_temperature() command. Once the protocol reaches the wait_for_tasks() command, the robot pauses for two minutes while the module holds at 75 °C.
    

    # 9. Shaking
    # Blocking
    #In this example, no other commands will execute until the Heater-Shaker reaches a shake speed of 500 RPM with the blocking command set_and_wait_for_shake_speed(). Because reaching the shake speed takes much less time than heating the module, these actions will take only about 85 seconds total. 这里85s total的意思应该是算上delay 1min，等于85s吧。
    hs_mod.set_and_wait_for_shake_speed(500)
    pipette_50.pick_up_tip()
    pipette_50.aspirate(50, plate_sample["A1"])
    pipette_50.dispense(50, plate_sample["B1"])
    pipette_50.drop_tip()
    protocol.delay(minutes=1)
    # Concurrent
    #To perform other actions while the module reaches its target temperature, use the concurrent set_target_temperature() command. Here, the robot will continue to perform pipetting steps and a protocol delay while the Heater-Shaker heats to 75 °C.
    hs_mod.set_shake_speed(500)
    pipette_50.pick_up_tip()
    pipette_50.aspirate(50, plate_sample["A1"])
    pipette_50.dispense(50, plate_sample["B1"])
    pipette_50.drop_tip()
    protocol.delay(minutes=1)
    #You can also use concurrent commands to heat and shake simultaneously. The amount of time it takes for the Heater-Shaker Module to reach either the target temperature or shake speed won't affect other steps in your protocol. The concurrent set_target_temperature() and set_shake_speed() methods also allow some other simultaneous module actions. 
    #由于本来就是两个功能，所以HS module本来就设计了两者可以同时执行。
    
    # 10. Deactivating
    #Deactivate the heater and shaker separately using the deactivate_heater() and deactivate_shaker() methods, respectively. There is no method to deactivate both simultaneously. Call the two methods in sequence if you need to stop both heating and shaking.
    #因为两个可以分别开，所以两个关的时候也要分别关。
    hs_mod.deactivate_heater()
    hs_mod.deactivate_shaker()
    #之前锁定了latch，所以要移除需要先解锁
    hs_mod.open_labware_latch()
    
    
    '''
    protocol.move_labware(labware=hs_adapter,new_location="C1",use_gripper=True)
    Gripper 只能抓取“顶层”的耗材——如果目标耗材上面还叠着其他非盖子(non-lid)耗材，它无法伸进去抓底下的适配器。此时 hs_adapter 上面还压着 hs_plate,所以抓取失败
    所以需要先抓取板子
    同理，如下也是不行的，因为不能直接抓adaptor
    protocol.move_labware(labware=plate_PCR,  new_location=hs_adaptor, use_gripper=True)
    protocol.move_labware(labware=hs_adaptor,  new_location=hs_mod, use_gripper=True)
    '''
    protocol.move_labware(labware=hs_plate,new_location="B1",use_gripper=False)
    protocol.move_labware(labware=hs_adapter,new_location="B2",use_gripper=False)
    hs_plate1 = protocol.load_labware("nest_96_wellplate_200ul_flat", "C1")
    hs_adapter1 = protocol.load_adapter("opentrons_96_flat_bottom_adapter","C3")
    hs_mod.set_and_wait_for_temperature(celsius=75)
    protocol.move_labware(labware=hs_adapter1,  new_location=hs_mod, use_gripper=False)
    protocol.move_labware(labware=hs_plate1,  new_location=hs_adapter1, use_gripper=False)  # adaptor有专门的适配板子，"opentrons_96_wellplate_200ul_pcr_full_skirt"板不能放到hs的适配器上
    hs_mod.close_labware_latch()   # 振荡前关锁扣
    hs_mod.set_shake_speed(500)
    
    '''
    另外提醒一句：实际运行时，load_adapter() 只是声明，铝制适配器是运行前就用螺丝固定在模块上的，不会在运行中途更换。你前面把第一个适配器手动移到 B2 的操作，在真实场景里对应的是“把板子取走、适配器留在模块上”。
    所以上面的流程用做练习就行了，真跑程序是不可能用这个的。
    '''
    
    '''
    1. 适配器不需要(也不能)用 Gripper 搬运。 Gripper 只兼容特定耗材：Opentrons Tough 系列耗材、Flex 吸头盒及盖、板盖、大多数平底板和 PCR 板、NEST 1 孔储液槽 docs.opentrons.com/gripper——适配器不在列表里；而且“适配器+板子”的组合定义被明确标记为 gripper 不兼容 github.com/13428。所以 move_labware(hs_adapter1, hs_mod, use_gripper=True) 这行应删掉。官方推荐的做法就是：适配器直接 load_adapter() 声明在模块上，Gripper 只负责把板子放上去 docs.opentrons.com/moving-labware。
    
    2. C3 已经被占用了。 你在第 1 步把 200 µL 吸头盒装在了 C3,即使改用 protocol.load_adapter(..., "C3") 也会报槽位冲突。
    
    3. 往模块上放板之前，必须先停摇、开锁扣。 你的协议在第 5 步就关锁扣并开始 500 RPM 振荡，之后一直没停。移板到模块上时锁扣是关着的、模块还在摇——这两条都会让 move_labware 报错(锁扣关闭时禁止向模块移入耗材 docs.opentrons.com/moving-labware)。
    
    4. 先加热后放板顺序反了。 你现在把空适配器加热到 75°C 再让 Gripper 把板子放上去，既不安全也没必要。应先放板、关锁扣，再加热和振荡。
    建议的写法
    
    # 先停摇、开锁扣,模块才允许被放入耗材
    hs_mod.deactivate_shaker()
    hs_mod.open_labware_latch()
    
    hs_plate1 = protocol.load_labware("nest_96_wellplate_200ul_flat", "C1")
    hs_adapter1 = hs_mod.load_adapter("opentrons_96_flat_bottom_adapter")  # 直接声明在模块上
    
    protocol.move_labware(labware=hs_plate1, new_location=hs_adapter1, use_gripper=True)  # Gripper只搬板子
    
    hs_mod.close_labware_latch()               # 振荡前关锁扣
    hs_mod.set_target_temperature(celsius=75)  # 先放板再加热
    hs_mod.set_shake_speed(500)
    
    '''
    
    
    
    