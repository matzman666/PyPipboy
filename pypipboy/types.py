# -*- coding: utf-8 -*-

class eMessageType:
    KEEP_ALIVE = 0
    CONNECTION_ACCEPTED = 1
    CONNECTION_REFUSED = 2
    DATA_UPDATE = 3
    LOCAL_MAP_UPDATE = 4
    COMMAND = 5
    COMMAND_RESULT = 6
    COUNT = 7


    
class eValueType:
    BOOL = 0
    INT_8 = 1
    UINT_8 = 2
    INT_32 = 3
    UINT_32 = 4
    FLOAT = 5
    STRING = 6
    ARRAY = 7
    OBJECT = 8
    

    
class eRequestType:
    UseItem = 0
    DropItem = 1
    SetFavorite = 2
    ToggleComponentFavorite = 3
    SortInventory = 4
    ToggleQuestActive = 5
    SetCustomMapMarker = 6
    RemoveCustomMapMarker = 7
    CheckFastTravel = 8
    FastTravel = 9
    MoveLocalMap = 10
    ZoomLocalMap = 11
    ToggleRadioStation = 12
    RequestLocalMapSnapshot = 13
    ClearIdle = 14
    
    
    
class eLocationMarkerType:
    CaveMarker  =  0
    CityMarker  =  1
    DiamondCityMarker  =  2
    EncampmentMarker  =  3
    FactoryMarker  =  4
    MonumentMarker  =  5
    MetroMarker  =  6
    MilitaryBaseMarker  =  7
    LandmarkMarker  =  8
    OfficeMarker  =  9
    TownRuinsMarker  =  10
    UrbanRuinsMarker  =  11
    SancHillsMarker  =  12
    SettlementMarker  =  13
    SewerMarker  =  14
    VaultMarker  =  15
    AirfieldMarker  =  16
    BunkerHillMarker  =  17
    CamperMarker  =  18
    CarMarker  =  19
    ChurchMarker  =  20
    CountryClubMarker  =  21
    CustomHouseMarker  =  22
    DriveInMarker  =  23
    ElevatedHighwayMarker  =  24
    FaneuilHallMarker  =  25
    FarmMarker  =  26
    FillingStationMarker  =  27
    ForestedMarker  =  28
    GoodneighborMarker  =  29
    GraveyardMarker  =  30
    HospitalMarker  =  31
    IndustrialDomeMarker  =  32
    IndustrialStacksMarker  =  33
    InstituteMarker  =  34
    IrishPrideMarker  =  35
    JunkyardMarker  =  36
    ObservatoryMarker  =  37
    PierMarker  =  38
    PondLakeMarker  =  39
    QuarryMarker  =  40
    RadioactiveAreaMarker  =  41
    RadioTowerMarker  =  42
    SalemMarker  =  43
    SchoolMarker  =  44
    ShipwreckMarker  =  45
    SubmarineMarker  =  46
    SwanPondMarker  =  47
    SynthHeadMarker  =  48
    TownMarker  =  49
    BoSMarker  =  50
    BrownstoneMarker  =  51
    BunkerMarker  =  52
    CastleMarker  =  53
    SkyscraperMarker  =  54
    LibertaliaMarker  =  55
    LowRiseMarker  =  56
    MinutemenMarker  =  57
    PoliceStationMarker  =  58
    PrydwenMarker  =  59
    RailroadFactionMarker  =  60
    RailroadMarker  =  61
    SatelliteMarker  =  62
    SentinelMarker  =  63
    USSConstitutionMarker  =  64
    DoorMarker  =  65
    QuestMarker  =  66
    QuestMarkerDoor  =  67
    QuestMarker  =  68
    PlayerSetMarker  =  69
    PlayerLocMarker  =  70
    PowerArmorLocMarker  =  71
    
    
    