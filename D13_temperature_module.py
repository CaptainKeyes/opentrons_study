from opentrons import protocol_api

metadata = {
    "protocolName": "D13:Temperature  Module加载 & adaptor和labware一起load",
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
    
    # 4. Load Temperature Module
    #The Temperature Module acts as both a cooling and heating device. It can control the temperature of its deck between 4 °C and 95 °C with a resolution of 1 °C.
    temp_mod = protocol.load_module(
        module_name="temperature module gen2", location="D3")
    
    # 5. Loading labware
    #Use the Temperature Module’s load_adapter() and load_labware() methods to specify what you will place on the module. 
    # Standalone adapters
    # You can use these standalone adapter definitions to load Opentrons verified or custom labware on top of the Temperature Module.（见python-api/modules/temperature-module/）
    temp_adapter = temp_mod.load_adapter(
        "opentrons_96_well_aluminum_block")
    temp_plate = temp_adapter.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt")
    '''
    # Loading together
    #你也可以一起loading到module上
    temp_plate1 = temp_mod.load_labware(
        name="biorad_96_wellplate_200ul_pcr",
        adapter="opentrons_96_well_aluminum_block")
    '''
    
    #Block-and-tube combinations
    # You can use these combination labware definitions to load various types of tubes into the 24-well thermal block on top of the Temperature Module. There is no standalone definition for the 24-well block.（在耗材的aluminum block中）
    #Block-and-plate combinations
    #The Temperature Module supports these 96-well block and labware combinations for backwards compatibility. If your protocol specifies an apiLevel of 2.15 or higher, you should use the standalone 96-well block definition instead.
    #那这是白说，因为我就是API 2.15以上。
    
    # 6. Temperature control
    #还是老一套
    #Blocking
    temp_mod.set_temperature(celsius=4)
    right_pipette.pick_up_tip()
    right_pipette.aspirate(50, plate_buffer["A1"])
    right_pipette.dispense(50, plate_buffer["B1"])
    right_pipette.drop_tip()
    #Concurrent
    temp_mod.start_set_temperature(celsius=4)
    right_pipette.pick_up_tip()
    right_pipette.aspirate(50, plate_buffer["A1"])
    right_pipette.dispense(50, plate_buffer["B1"])
    right_pipette.mix(repetitions=3,volume=30,location=plate_buffer["B1"].bottom(z=1.4))
    right_pipette.drop_tip()
    
    # 7. Temperature status
    #If you need to confirm in software whether the Temperature Module is holding at a temperature or is idle, use the status property:
    temp_mod.set_temperature(celsius=90)
    temp_mod.status  # "holding at target"
    temp_mod.deactivate()
    temp_mod.status  # "idle"
    #没有任何用，只是检查状态
    
        
    
    
    