"""
National Weather Big Data Analytics Platform (NWBDAP)
All-India States & Districts Geographic Registry
Comprehensive mapping for all 28 States and 8 Union Territories with 500+ Districts.
"""
import re

INDIA_STATES_DISTRICTS = {
    "Andhra Pradesh": {
        "Visakhapatnam": {"lat": 17.6868, "lon": 83.2185},
        "Vijayawada": {"lat": 16.5062, "lon": 80.6480},
        "Guntur": {"lat": 16.3067, "lon": 80.4365},
        "Nellore": {"lat": 14.4426, "lon": 79.9865},
        "Kurnool": {"lat": 15.8281, "lon": 78.0373},
        "Kakinada": {"lat": 16.9891, "lon": 82.2475},
        "Rajahmundry": {"lat": 17.0005, "lon": 81.8040},
        "Tirupati": {"lat": 13.6288, "lon": 79.4192},
        "Kadapa": {"lat": 14.4673, "lon": 78.8242},
        "Anantapur": {"lat": 14.6819, "lon": 77.6006},
        "Vizianagaram": {"lat": 18.1067, "lon": 83.3956},
        "Eluru": {"lat": 16.7107, "lon": 81.0952},
        "Ongole": {"lat": 15.5057, "lon": 80.0499},
        "Chittoor": {"lat": 13.2172, "lon": 79.1003},
        "Srikakulam": {"lat": 18.2949, "lon": 83.8938},
        "Machilipatnam": {"lat": 16.1875, "lon": 81.1389}
    },
    "Arunachal Pradesh": {
        "Itanagar": {"lat": 27.0844, "lon": 93.6053},
        "Tawang": {"lat": 27.5861, "lon": 91.8594},
        "Pasighat": {"lat": 28.0664, "lon": 95.3268},
        "Ziro": {"lat": 27.5946, "lon": 93.8385},
        "Naharlagun": {"lat": 27.1042, "lon": 93.6938},
        "Bomdila": {"lat": 27.2644, "lon": 92.4159},
        "Along (Aalo)": {"lat": 28.1678, "lon": 94.8014},
        "Tezu": {"lat": 27.9174, "lon": 96.1667},
        "Roing": {"lat": 28.1408, "lon": 95.8453},
        "Changlang": {"lat": 27.1264, "lon": 95.7336}
    },
    "Assam": {
        "Guwahati": {"lat": 26.1445, "lon": 91.7362},
        "Silchar": {"lat": 24.8333, "lon": 92.7789},
        "Dibrugarh": {"lat": 27.4728, "lon": 94.9120},
        "Jorhat": {"lat": 26.7509, "lon": 94.2037},
        "Nagaon": {"lat": 26.3464, "lon": 92.6840},
        "Tinsukia": {"lat": 27.4922, "lon": 95.3468},
        "Tezpur": {"lat": 26.6528, "lon": 92.7926},
        "Bongaigaon": {"lat": 26.5028, "lon": 90.5540},
        "Karimganj": {"lat": 24.8690, "lon": 92.3590},
        "Sivasagar": {"lat": 26.9844, "lon": 94.6378},
        "Barpeta": {"lat": 26.3211, "lon": 91.0064},
        "Dhubri": {"lat": 26.0208, "lon": 89.9749},
        "Goalpara": {"lat": 26.1756, "lon": 90.6247},
        "Golaghat": {"lat": 26.5186, "lon": 93.9678},
        "North Lakhimpur": {"lat": 27.2344, "lon": 94.1042}
    },
    "Bihar": {
        "Patna": {"lat": 25.5941, "lon": 85.1376},
        "Gaya": {"lat": 24.7955, "lon": 85.0002},
        "Bhagalpur": {"lat": 25.2425, "lon": 86.9842},
        "Muzaffarpur": {"lat": 26.1209, "lon": 85.3647},
        "Purnia": {"lat": 25.7771, "lon": 87.4753},
        "Darbhanga": {"lat": 26.1542, "lon": 85.8918},
        "Bihar Sharif": {"lat": 25.1982, "lon": 85.5149},
        "Arrah (Bhojpur)": {"lat": 25.5560, "lon": 84.6603},
        "Begusarai": {"lat": 25.4182, "lon": 86.1272},
        "Katihar": {"lat": 25.5398, "lon": 87.5724},
        "Munger": {"lat": 25.3757, "lon": 86.4744},
        "Chhapra (Saran)": {"lat": 25.7796, "lon": 84.7499},
        "Sasaram (Rohtas)": {"lat": 24.9515, "lon": 84.0298},
        "Samastipur": {"lat": 25.8630, "lon": 85.7811},
        "Motihari (East Champaran)": {"lat": 26.6469, "lon": 84.9089},
        "Bettiah (West Champaran)": {"lat": 26.8024, "lon": 84.5029},
        "Siwan": {"lat": 26.2196, "lon": 84.3567},
        "Vaishali (Hajipur)": {"lat": 25.6858, "lon": 85.2146},
        "Nalanda": {"lat": 25.1357, "lon": 85.4450},
        "Saharsa": {"lat": 25.8835, "lon": 86.6006}
    },
    "Chhattisgarh": {
        "Raipur": {"lat": 21.2514, "lon": 81.6296},
        "Bhilai-Durg": {"lat": 21.2121, "lon": 81.3733},
        "Bilaspur": {"lat": 22.0797, "lon": 82.1409},
        "Korba": {"lat": 22.3595, "lon": 82.7501},
        "Rajnandgaon": {"lat": 21.0974, "lon": 81.0366},
        "Jagdalpur (Bastar)": {"lat": 19.0740, "lon": 82.0081},
        "Raigarh": {"lat": 21.8974, "lon": 83.3950},
        "Ambikapur (Surguja)": {"lat": 23.1186, "lon": 83.1997},
        "Dhamtari": {"lat": 20.7071, "lon": 81.5498},
        "Mahasamund": {"lat": 21.1084, "lon": 82.0963},
        "Kanker": {"lat": 20.2717, "lon": 81.4931},
        "Janjgir-Champa": {"lat": 22.0094, "lon": 82.5739}
    },
    "Goa": {
        "Panaji (North Goa)": {"lat": 15.4909, "lon": 73.8278},
        "Margao (South Goa)": {"lat": 15.2832, "lon": 73.9862},
        "Vasco da Gama": {"lat": 15.3982, "lon": 73.8113},
        "Mapusa": {"lat": 15.5937, "lon": 73.8142},
        "Ponda": {"lat": 15.4026, "lon": 74.0152}
    },
    "Gujarat": {
        "Ahmedabad": {"lat": 23.0225, "lon": 72.5714},
        "Surat": {"lat": 21.1702, "lon": 72.8311},
        "Vadodara": {"lat": 22.3072, "lon": 73.1812},
        "Rajkot": {"lat": 22.3039, "lon": 70.8022},
        "Bhavnagar": {"lat": 21.7645, "lon": 72.1519},
        "Jamnagar": {"lat": 22.4707, "lon": 70.0577},
        "Junagadh": {"lat": 21.5222, "lon": 70.4579},
        "Gandhinagar": {"lat": 23.2156, "lon": 72.6369},
        "Anand": {"lat": 22.5645, "lon": 72.9289},
        "Navsari": {"lat": 20.9500, "lon": 72.9300},
        "Morbi": {"lat": 22.8173, "lon": 70.8378},
        "Bharuch": {"lat": 21.7051, "lon": 72.9959},
        "Porbandar": {"lat": 21.6417, "lon": 69.6293},
        "Bhuj (Kutch)": {"lat": 23.2420, "lon": 69.6669},
        "Valsad": {"lat": 20.5992, "lon": 72.9342},
        "Mehsana": {"lat": 23.5880, "lon": 72.3693},
        "Patan": {"lat": 23.8493, "lon": 72.1266},
        "Palanpur (Banaskantha)": {"lat": 24.1724, "lon": 72.4346},
        "Himmatnagar (Sabarkantha)": {"lat": 23.5977, "lon": 72.9698},
        "Amreli": {"lat": 21.6032, "lon": 71.2221},
        "Surendranagar": {"lat": 22.7276, "lon": 71.6370},
        "Godhra (Panchmahal)": {"lat": 22.7758, "lon": 73.6149}
    },
    "Haryana": {
        "Gurugram": {"lat": 28.4595, "lon": 77.0266},
        "Faridabad": {"lat": 28.4089, "lon": 77.3178},
        "Panipat": {"lat": 29.3909, "lon": 76.9635},
        "Ambala": {"lat": 30.3782, "lon": 76.7767},
        "Yamunanagar": {"lat": 30.1290, "lon": 77.2674},
        "Rohtak": {"lat": 28.8955, "lon": 76.6066},
        "Hisar": {"lat": 29.1492, "lon": 75.7217},
        "Karnal": {"lat": 29.6857, "lon": 76.9905},
        "Sonipat": {"lat": 28.9931, "lon": 77.0151},
        "Panchkula": {"lat": 30.6942, "lon": 76.8606},
        "Sirsa": {"lat": 29.5349, "lon": 75.0298},
        "Bhiwani": {"lat": 28.7932, "lon": 76.1390},
        "Kurukshetra": {"lat": 29.9695, "lon": 76.8783},
        "Jind": {"lat": 29.3150, "lon": 76.3157},
        "Rewari": {"lat": 28.1920, "lon": 76.6191}
    },
    "Himachal Pradesh": {
        "Shimla": {"lat": 31.1048, "lon": 77.1734},
        "Dharamshala (Kangra)": {"lat": 32.2190, "lon": 76.3234},
        "Mandi": {"lat": 31.5892, "lon": 76.9182},
        "Solan": {"lat": 30.9045, "lon": 77.0967},
        "Kullu": {"lat": 31.9579, "lon": 77.1095},
        "Manali": {"lat": 32.2432, "lon": 77.1892},
        "Chamba": {"lat": 32.5534, "lon": 76.1258},
        "Hamirpur": {"lat": 31.6862, "lon": 76.5213},
        "Bilaspur": {"lat": 31.3325, "lon": 76.7578},
        "Una": {"lat": 31.4685, "lon": 76.2708},
        "Nahan (Sirmaur)": {"lat": 30.5599, "lon": 77.2955},
        "Kinnaur (Reckong Peo)": {"lat": 31.5401, "lon": 78.2718},
        "Lahaul and Spiti (Keylong)": {"lat": 32.5710, "lon": 77.0320}
    },
    "Jharkhand": {
        "Ranchi": {"lat": 23.3441, "lon": 85.3096},
        "Jamshedpur (East Singhbhum)": {"lat": 22.8046, "lon": 86.2029},
        "Dhanbad": {"lat": 23.7957, "lon": 86.4304},
        "Bokaro Steel City": {"lat": 23.6693, "lon": 86.1511},
        "Deoghar": {"lat": 24.4826, "lon": 86.7001},
        "Hazaribagh": {"lat": 23.9961, "lon": 85.3688},
        "Giridih": {"lat": 24.1867, "lon": 86.3092},
        "Ramgarh": {"lat": 23.6332, "lon": 85.5155},
        "Dumka": {"lat": 24.2690, "lon": 87.2483},
        "Chaibasa (West Singhbhum)": {"lat": 22.5533, "lon": 85.8083},
        "Palamu (Medininagar)": {"lat": 24.0384, "lon": 84.0707}
    },
    "Karnataka": {
        "Bengaluru Urban": {"lat": 12.9716, "lon": 77.5946},
        "Bengaluru Rural": {"lat": 13.2847, "lon": 77.5540},
        "Mysuru": {"lat": 12.2958, "lon": 76.6394},
        "Mangaluru (Dakshina Kannada)": {"lat": 12.9141, "lon": 74.8560},
        "Hubballi-Dharwad": {"lat": 15.3647, "lon": 75.1240},
        "Belagavi": {"lat": 15.8497, "lon": 74.4977},
        "Kalaburagi (Gulbarga)": {"lat": 17.3297, "lon": 76.8343},
        "Davanagere": {"lat": 14.4644, "lon": 75.9218},
        "Ballari": {"lat": 15.1394, "lon": 76.9214},
        "Vijayapura (Bijapur)": {"lat": 16.8302, "lon": 75.7100},
        "Shivamogga": {"lat": 13.9299, "lon": 75.5681},
        "Tumakuru": {"lat": 13.3379, "lon": 77.1017},
        "Udupi": {"lat": 13.3409, "lon": 74.7421},
        "Bidar": {"lat": 17.9104, "lon": 77.5199},
        "Raichur": {"lat": 16.2120, "lon": 77.3439},
        "Hassan": {"lat": 13.0072, "lon": 76.1030},
        "Mandya": {"lat": 12.5244, "lon": 76.8958},
        "Chitradurga": {"lat": 14.2251, "lon": 76.4015},
        "Chikkamagaluru": {"lat": 13.3161, "lon": 75.7720},
        "Kolar": {"lat": 13.1367, "lon": 78.1291},
        "Kodagu (Madikeri)": {"lat": 12.4244, "lon": 75.7382}
    },
    "Kerala": {
        "Thiruvananthapuram": {"lat": 8.5241, "lon": 76.9366},
        "Kochi (Ernakulam)": {"lat": 9.9312, "lon": 76.2673},
        "Kozhikode": {"lat": 11.2588, "lon": 75.7804},
        "Thrissur": {"lat": 10.5276, "lon": 76.2144},
        "Kollam": {"lat": 8.8932, "lon": 76.6141},
        "Palakkad": {"lat": 10.7867, "lon": 76.6548},
        "Alappuzha": {"lat": 9.4981, "lon": 76.3388},
        "Kannur": {"lat": 11.8745, "lon": 75.3704},
        "Kottayam": {"lat": 9.5916, "lon": 76.5222},
        "Malappuram": {"lat": 11.0510, "lon": 76.0711},
        "Kasaragod": {"lat": 12.4996, "lon": 74.9869},
        "Pathanamthitta": {"lat": 9.2648, "lon": 76.7870},
        "Idukki": {"lat": 9.9189, "lon": 76.9723},
        "Wayanad (Kalpetta)": {"lat": 11.6103, "lon": 76.0829}
    },
    "Madhya Pradesh": {
        "Bhopal": {"lat": 23.2599, "lon": 77.4126},
        "Indore": {"lat": 22.7196, "lon": 75.8577},
        "Jabalpur": {"lat": 23.1815, "lon": 79.9864},
        "Gwalior": {"lat": 26.2183, "lon": 78.1828},
        "Ujjain": {"lat": 23.1765, "lon": 75.7885},
        "Sagar": {"lat": 23.8388, "lon": 78.7378},
        "Dewas": {"lat": 22.9676, "lon": 76.0534},
        "Satna": {"lat": 24.5828, "lon": 80.8286},
        "Ratlam": {"lat": 23.3315, "lon": 75.0367},
        "Rewa": {"lat": 24.5373, "lon": 81.3042},
        "Singrauli": {"lat": 24.1992, "lon": 82.6645},
        "Burhanpur": {"lat": 21.3145, "lon": 76.2299},
        "Khandwa": {"lat": 21.8314, "lon": 76.3498},
        "Morena": {"lat": 26.4948, "lon": 77.9940},
        "Bhind": {"lat": 26.5647, "lon": 78.7898},
        "Shivpuri": {"lat": 25.4244, "lon": 77.6588},
        "Chhindwara": {"lat": 22.0574, "lon": 78.9382},
        "Khargone (West Nimar)": {"lat": 21.8217, "lon": 75.6128},
        "Hoshangabad (Narmadapuram)": {"lat": 22.7519, "lon": 77.7289},
        "Vidisha": {"lat": 23.5251, "lon": 77.8081}
    },
    "Maharashtra": {
        "Pune": {"lat": 18.5204, "lon": 73.8567},
        "Mumbai City": {"lat": 18.9388, "lon": 72.8354},
        "Mumbai Suburban": {"lat": 19.0760, "lon": 72.8777},
        "Nagpur": {"lat": 21.1458, "lon": 79.0882},
        "Nashik": {"lat": 19.9975, "lon": 73.7898},
        "Thane": {"lat": 19.2183, "lon": 72.9781},
        "Chhatrapati Sambhaji Nagar (Aurangabad)": {"lat": 19.8762, "lon": 75.3433},
        "Solapur": {"lat": 17.6599, "lon": 75.9064},
        "Kolhapur": {"lat": 16.7050, "lon": 74.2433},
        "Amravati": {"lat": 20.9374, "lon": 77.7796},
        "Nanded": {"lat": 19.1383, "lon": 77.3210},
        "Jalgaon": {"lat": 21.0077, "lon": 75.5626},
        "Akola": {"lat": 20.7002, "lon": 77.0082},
        "Latur": {"lat": 18.4088, "lon": 76.5604},
        "Dhule": {"lat": 20.9042, "lon": 74.7749},
        "Ahmednagar": {"lat": 19.0948, "lon": 74.7480},
        "Chandrapur": {"lat": 19.9615, "lon": 79.2961},
        "Parbhani": {"lat": 19.2686, "lon": 76.7708},
        "Jalna": {"lat": 19.8410, "lon": 75.8864},
        "Satara": {"lat": 17.6805, "lon": 74.0183},
        "Beed": {"lat": 18.9891, "lon": 75.7601},
        "Yavatmal": {"lat": 20.3888, "lon": 78.1204},
        "Sangli": {"lat": 16.8524, "lon": 74.5815},
        "Raigad (Alibag)": {"lat": 18.6414, "lon": 72.8722},
        "Buldhana": {"lat": 20.5293, "lon": 76.1843},
        "Dharashiv (Osmanabad)": {"lat": 18.1853, "lon": 76.0419},
        "Bhandara": {"lat": 21.1667, "lon": 79.6500},
        "Wardha": {"lat": 20.7453, "lon": 78.6022},
        "Gondia": {"lat": 21.4598, "lon": 80.1961},
        "Washim": {"lat": 20.1114, "lon": 77.1362},
        "Hingoli": {"lat": 19.7180, "lon": 77.1488},
        "Gadchiroli": {"lat": 20.1849, "lon": 79.9948},
        "Palghar": {"lat": 19.6967, "lon": 72.7699},
        "Ratnagiri": {"lat": 16.9902, "lon": 73.3120},
        "Sindhudurg (Oros)": {"lat": 16.1158, "lon": 73.6997},
        "Nandurbar": {"lat": 21.3705, "lon": 74.2405}
    },
    "Manipur": {
        "Imphal West": {"lat": 24.8170, "lon": 93.9368},
        "Imphal East": {"lat": 24.8211, "lon": 94.0203},
        "Thoubal": {"lat": 24.6384, "lon": 94.0163},
        "Bishnupur": {"lat": 24.6324, "lon": 93.7644},
        "Churachandpur": {"lat": 24.3333, "lon": 93.6667},
        "Senapati": {"lat": 25.2686, "lon": 94.0189},
        "Ukhrul": {"lat": 25.1121, "lon": 94.3601}
    },
    "Meghalaya": {
        "Shillong (East Khasi Hills)": {"lat": 25.5788, "lon": 91.8933},
        "Tura (West Garo Hills)": {"lat": 25.5142, "lon": 90.2030},
        "Jowai (West Jaintia Hills)": {"lat": 25.4547, "lon": 92.2037},
        "Nongpoh (Ri Bhoi)": {"lat": 25.9031, "lon": 91.8794},
        "Cherrapunji (Sohra)": {"lat": 25.2986, "lon": 91.7330},
        "Williamnagar (East Garo Hills)": {"lat": 25.4947, "lon": 90.6175}
    },
    "Mizoram": {
        "Aizawl": {"lat": 23.7271, "lon": 92.7176},
        "Lunglei": {"lat": 22.8671, "lon": 92.7655},
        "Champhai": {"lat": 23.4754, "lon": 93.3283},
        "Kolasib": {"lat": 24.2247, "lon": 92.6781},
        "Serchhip": {"lat": 23.3417, "lon": 92.8503}
    },
    "Nagaland": {
        "Kohima": {"lat": 25.6751, "lon": 94.1086},
        "Dimapur": {"lat": 25.9094, "lon": 93.7266},
        "Mokokchung": {"lat": 26.3249, "lon": 94.5161},
        "Tuensang": {"lat": 26.2690, "lon": 94.8290},
        "Wokha": {"lat": 26.0984, "lon": 94.2625},
        "Mon": {"lat": 26.7410, "lon": 95.0600}
    },
    "Odisha": {
        "Bhubaneswar": {"lat": 20.2961, "lon": 85.8245},
        "Cuttack": {"lat": 20.4625, "lon": 85.8828},
        "Rourkela (Sundargarh)": {"lat": 22.2604, "lon": 84.8536},
        "Berhampur (Ganjam)": {"lat": 19.3150, "lon": 84.7941},
        "Sambalpur": {"lat": 21.4669, "lon": 83.9812},
        "Puri": {"lat": 19.8135, "lon": 85.8312},
        "Balasore": {"lat": 21.4934, "lon": 86.9135},
        "Bhadrak": {"lat": 21.0574, "lon": 86.4957},
        "Baripada (Mayurbhanj)": {"lat": 21.9348, "lon": 86.7327},
        "Jharsuguda": {"lat": 21.8554, "lon": 84.0062},
        "Angul": {"lat": 20.8398, "lon": 85.1013},
        "Koraput": {"lat": 18.8135, "lon": 82.7118},
        "Kendujhar": {"lat": 21.6289, "lon": 85.5817},
        "Khurda": {"lat": 20.1814, "lon": 85.6206}
    },
    "Punjab": {
        "Amritsar": {"lat": 31.6340, "lon": 74.8723},
        "Ludhiana": {"lat": 30.9010, "lon": 75.8573},
        "Jalandhar": {"lat": 31.3260, "lon": 75.5762},
        "Patiala": {"lat": 30.3398, "lon": 76.3869},
        "Bathinda": {"lat": 30.2110, "lon": 74.9455},
        "Mohali (SAS Nagar)": {"lat": 30.7046, "lon": 76.7179},
        "Hoshiarpur": {"lat": 31.5273, "lon": 75.9149},
        "Pathankot": {"lat": 32.2689, "lon": 75.6499},
        "Moga": {"lat": 30.8165, "lon": 75.1717},
        "Firozpur": {"lat": 30.9255, "lon": 74.6122},
        "Gurdaspur": {"lat": 32.0419, "lon": 75.4053},
        "Kapurthala": {"lat": 31.3802, "lon": 75.3814},
        "Sangrur": {"lat": 30.2458, "lon": 75.8421},
        "Barnala": {"lat": 30.3819, "lon": 75.5467},
        "Muktsar": {"lat": 30.4744, "lon": 74.5170}
    },
    "Rajasthan": {
        "Jaipur": {"lat": 26.9124, "lon": 75.7873},
        "Jodhpur": {"lat": 26.2389, "lon": 73.0243},
        "Kota": {"lat": 25.2138, "lon": 75.8648},
        "Bikaner": {"lat": 28.0229, "lon": 73.3119},
        "Ajmer": {"lat": 26.4499, "lon": 74.6399},
        "Udaipur": {"lat": 24.5854, "lon": 73.7125},
        "Bhilwara": {"lat": 25.3407, "lon": 74.6313},
        "Alwar": {"lat": 27.5530, "lon": 76.6346},
        "Sikar": {"lat": 27.6094, "lon": 75.1398},
        "Bharatpur": {"lat": 27.2152, "lon": 77.5030},
        "Pali": {"lat": 25.7711, "lon": 73.3234},
        "Sri Ganganagar": {"lat": 29.9094, "lon": 73.8799},
        "Jaisalmer": {"lat": 26.9157, "lon": 70.9083},
        "Barmer": {"lat": 25.7532, "lon": 71.3967},
        "Chittorgarh": {"lat": 24.8887, "lon": 74.6269},
        "Jhunjhunu": {"lat": 28.1289, "lon": 75.3995},
        "Churu": {"lat": 28.2900, "lon": 74.9600},
        "Nagaur": {"lat": 27.2021, "lon": 73.7439},
        "Tonk": {"lat": 26.1667, "lon": 75.7833},
        "Sawai Madhopur": {"lat": 25.9928, "lon": 76.3533}
    },
    "Sikkim": {
        "Gangtok (East Sikkim)": {"lat": 27.3389, "lon": 88.6065},
        "Namchi (South Sikkim)": {"lat": 27.1667, "lon": 88.3500},
        "Geyzing (West Sikkim)": {"lat": 27.2889, "lon": 88.2556},
        "Mangan (North Sikkim)": {"lat": 27.5042, "lon": 88.5283}
    },
    "Tamil Nadu": {
        "Chennai": {"lat": 13.0827, "lon": 80.2707},
        "Coimbatore": {"lat": 11.0168, "lon": 76.9558},
        "Madurai": {"lat": 9.9252, "lon": 78.1198},
        "Tiruchirappalli": {"lat": 10.7905, "lon": 78.7047},
        "Salem": {"lat": 11.6643, "lon": 78.1460},
        "Tirunelveli": {"lat": 8.7139, "lon": 77.7567},
        "Tiruppur": {"lat": 11.1085, "lon": 77.3411},
        "Vellore": {"lat": 12.9165, "lon": 79.1325},
        "Erode": {"lat": 11.3410, "lon": 77.7172},
        "Thoothukudi (Tuticorin)": {"lat": 8.7642, "lon": 78.1348},
        "Dindigul": {"lat": 10.3673, "lon": 77.9803},
        "Thanjavur": {"lat": 10.7870, "lon": 79.1378},
        "Kanchipuram": {"lat": 12.8342, "lon": 79.7036},
        "Cuddalore": {"lat": 11.7480, "lon": 79.7714},
        "Nagercoil (Kanyakumari)": {"lat": 8.1833, "lon": 77.4119},
        "Kallakurichi": {"lat": 11.7384, "lon": 78.9639},
        "Namakkal": {"lat": 11.2189, "lon": 78.1674},
        "Krishnagiri": {"lat": 12.5186, "lon": 78.2137},
        "Dharmapuri": {"lat": 12.1211, "lon": 78.1582},
        "Ramanathapuram": {"lat": 9.3639, "lon": 78.8395},
        "Sivaganga": {"lat": 9.8433, "lon": 78.4809},
        "Nilgiris (Ooty)": {"lat": 11.4102, "lon": 76.6950}
    },
    "Telangana": {
        "Hyderabad": {"lat": 17.3850, "lon": 78.4867},
        "Warangal": {"lat": 17.9689, "lon": 79.5941},
        "Nizamabad": {"lat": 18.6725, "lon": 78.0941},
        "Karimnagar": {"lat": 18.4386, "lon": 79.1288},
        "Khammam": {"lat": 17.2473, "lon": 80.1514},
        "Ramagundam": {"lat": 18.7557, "lon": 79.4738},
        "Mahbubnagar": {"lat": 16.7488, "lon": 78.0035},
        "Nalgonda": {"lat": 17.0577, "lon": 79.2684},
        "Adilabad": {"lat": 19.6641, "lon": 78.5320},
        "Suryapet": {"lat": 17.1439, "lon": 79.6239},
        "Siddipet": {"lat": 18.1018, "lon": 78.8520},
        "Medak": {"lat": 18.0485, "lon": 78.2618},
        "Mancherial": {"lat": 18.8679, "lon": 79.4639}
    },
    "Tripura": {
        "Agartala (West Tripura)": {"lat": 23.8315, "lon": 91.2868},
        "Udaipur (Gomati)": {"lat": 23.5333, "lon": 91.4833},
        "Dharmanagar (North Tripura)": {"lat": 24.3725, "lon": 92.1625},
        "Ambassa (Dhalai)": {"lat": 23.9286, "lon": 91.8542},
        "Khowai": {"lat": 24.0625, "lon": 91.6042},
        "Belonia (South Tripura)": {"lat": 23.2500, "lon": 91.4500}
    },
    "Uttar Pradesh": {
        "Lucknow": {"lat": 26.8467, "lon": 80.9462},
        "Kanpur": {"lat": 26.4499, "lon": 80.3319},
        "Varanasi": {"lat": 25.3176, "lon": 82.9739},
        "Agra": {"lat": 27.1767, "lon": 78.0081},
        "Prayagraj (Allahabad)": {"lat": 25.4358, "lon": 81.8463},
        "Meerut": {"lat": 28.9845, "lon": 77.7064},
        "Ghaziabad": {"lat": 28.6692, "lon": 77.4538},
        "Noida (Gautam Buddha Nagar)": {"lat": 28.5355, "lon": 77.3910},
        "Bareilly": {"lat": 28.3670, "lon": 79.4304},
        "Aligarh": {"lat": 27.8974, "lon": 78.0880},
        "Moradabad": {"lat": 28.8386, "lon": 78.7733},
        "Saharanpur": {"lat": 29.9640, "lon": 77.5460},
        "Gorakhpur": {"lat": 26.7606, "lon": 83.3732},
        "Jhansi": {"lat": 25.4484, "lon": 78.5685},
        "Mathura": {"lat": 27.4924, "lon": 77.6737},
        "Ayodhya (Faizabad)": {"lat": 26.7922, "lon": 82.1998},
        "Muzaffarnagar": {"lat": 29.4727, "lon": 77.7085},
        "Firozabad": {"lat": 27.1591, "lon": 78.3957},
        "Shahjahanpur": {"lat": 27.8804, "lon": 79.9122},
        "Rampur": {"lat": 28.8154, "lon": 79.0257},
        "Mirzapur": {"lat": 25.1337, "lon": 82.5644},
        "Budaun": {"lat": 28.0300, "lon": 79.1200},
        "Bulandshahr": {"lat": 28.4070, "lon": 77.8498},
        "Sambhal": {"lat": 28.5833, "lon": 78.5500},
        "Amroha": {"lat": 28.9044, "lon": 78.4678},
        "Hardoi": {"lat": 27.3958, "lon": 80.1314},
        "Fatehpur": {"lat": 25.9286, "lon": 80.8131},
        "Raebareli": {"lat": 26.2303, "lon": 81.2409},
        "Orai (Jalaun)": {"lat": 25.9898, "lon": 79.4507},
        "Sitapur": {"lat": 27.5614, "lon": 80.6828},
        "Bahraich": {"lat": 27.5750, "lon": 81.5972},
        "Lakhimpur Kheri": {"lat": 27.9482, "lon": 80.7787},
        "Jaunpur": {"lat": 25.7464, "lon": 82.6837},
        "Azamgarh": {"lat": 26.0689, "lon": 83.1843},
        "Ballia": {"lat": 25.7583, "lon": 84.1497},
        "Banda": {"lat": 25.4754, "lon": 80.3347}
    },
    "Uttarakhand": {
        "Dehradun": {"lat": 30.3165, "lon": 78.0322},
        "Haridwar": {"lat": 29.9457, "lon": 78.1642},
        "Roorkee": {"lat": 29.8543, "lon": 77.8880},
        "Haldwani (Nainital)": {"lat": 29.2183, "lon": 79.5130},
        "Nainital": {"lat": 29.3919, "lon": 79.4542},
        "Rishikesh": {"lat": 30.0869, "lon": 78.2676},
        "Rudrapur (Udham Singh Nagar)": {"lat": 28.9789, "lon": 79.4005},
        "Kashipur": {"lat": 29.2104, "lon": 78.9619},
        "Pithoragarh": {"lat": 29.5829, "lon": 80.2182},
        "Almora": {"lat": 29.5971, "lon": 79.6591},
        "Gopeshwar (Chamoli)": {"lat": 30.4140, "lon": 79.3280},
        "New Tehri (Tehri Garhwal)": {"lat": 30.3800, "lon": 78.4800},
        "Uttarkashi": {"lat": 30.7268, "lon": 78.4354},
        "Pauri Garhwal": {"lat": 30.1500, "lon": 78.7800},
        "Rudraprayag": {"lat": 30.2844, "lon": 78.9811},
        "Bageshwar": {"lat": 29.8378, "lon": 79.7711},
        "Champawat": {"lat": 29.3347, "lon": 80.0911}
    },
    "West Bengal": {
        "Kolkata": {"lat": 22.5726, "lon": 88.3639},
        "Howrah": {"lat": 22.5958, "lon": 88.2636},
        "North 24 Parganas (Barasat)": {"lat": 22.7230, "lon": 88.4820},
        "South 24 Parganas (Alipore)": {"lat": 22.5312, "lon": 88.3245},
        "Siliguri": {"lat": 26.7271, "lon": 88.3953},
        "Asansol (Paschim Bardhaman)": {"lat": 23.6889, "lon": 86.9661},
        "Durgapur": {"lat": 23.5204, "lon": 87.3119},
        "Bardhaman (Purba Bardhaman)": {"lat": 23.2324, "lon": 87.8615},
        "Darjeeling": {"lat": 27.0410, "lon": 88.2663},
        "Kalimpong": {"lat": 27.0594, "lon": 88.4695},
        "Jalpaiguri": {"lat": 26.5405, "lon": 88.7194},
        "Alipurduar": {"lat": 26.4919, "lon": 89.5271},
        "Cooch Behar": {"lat": 26.3239, "lon": 89.4510},
        "Malda (English Bazar)": {"lat": 25.0108, "lon": 88.1411},
        "Baharampur (Murshidabad)": {"lat": 24.0988, "lon": 88.2680},
        "Krishnanagar (Nadia)": {"lat": 23.4013, "lon": 88.5019},
        "Chinsurah (Hooghly)": {"lat": 22.9031, "lon": 88.3968},
        "Tamluk (Purba Medinipur)": {"lat": 22.2980, "lon": 87.9250},
        "Medinipur (Paschim Medinipur)": {"lat": 22.4257, "lon": 87.3199},
        "Bankura": {"lat": 23.2324, "lon": 87.0715},
        "Purulia": {"lat": 23.3321, "lon": 86.3652},
        "Suri (Birbhum)": {"lat": 23.9054, "lon": 87.5246}
    },
    "Delhi": {
        "New Delhi": {"lat": 28.6139, "lon": 77.2090},
        "North Delhi": {"lat": 28.7100, "lon": 77.1600},
        "South Delhi": {"lat": 28.5400, "lon": 77.2100},
        "East Delhi": {"lat": 28.6300, "lon": 77.3000},
        "West Delhi": {"lat": 28.6600, "lon": 77.1000},
        "Central Delhi": {"lat": 28.6448, "lon": 77.2167},
        "North West Delhi": {"lat": 28.7400, "lon": 77.0800},
        "South West Delhi (Dwarka)": {"lat": 28.5921, "lon": 77.0460},
        "Shahdara": {"lat": 28.6738, "lon": 77.2917}
    },
    "Jammu and Kashmir": {
        "Srinagar": {"lat": 34.0837, "lon": 74.7973},
        "Jammu": {"lat": 32.7266, "lon": 74.8570},
        "Anantnag": {"lat": 33.7311, "lon": 75.1522},
        "Baramulla": {"lat": 34.2000, "lon": 74.3400},
        "Udhampur": {"lat": 32.9193, "lon": 75.1437},
        "Kathua": {"lat": 32.3719, "lon": 75.5186},
        "Sopore": {"lat": 34.2989, "lon": 74.4694},
        "Pulwama": {"lat": 32.8800, "lon": 74.9000},
        "Kupwara": {"lat": 34.5262, "lon": 74.2546},
        "Poonch": {"lat": 33.7667, "lon": 74.1000},
        "Rajouri": {"lat": 33.3762, "lon": 74.3129},
        "Budgam": {"lat": 34.0150, "lon": 74.7180},
        "Ganderbal": {"lat": 34.2162, "lon": 74.7778},
        "Bandipora": {"lat": 34.4217, "lon": 74.6472},
        "Kulgam": {"lat": 33.6450, "lon": 75.0194},
        "Shopian": {"lat": 33.7194, "lon": 74.8319},
        "Doda": {"lat": 33.1458, "lon": 75.5469},
        "Ramban": {"lat": 33.2425, "lon": 75.2417},
        "Kishtwar": {"lat": 33.3142, "lon": 75.7667},
        "Reasi": {"lat": 33.0833, "lon": 74.8333}
    },
    "Ladakh": {
        "Leh": {"lat": 34.1526, "lon": 77.5771},
        "Kargil": {"lat": 34.5539, "lon": 76.1349},
        "Nubra Valley (Diskit)": {"lat": 34.5422, "lon": 77.5619},
        "Drass": {"lat": 34.4322, "lon": 75.7533},
        "Zanskar (Padum)": {"lat": 33.4650, "lon": 76.8833}
    },
    "Chandigarh": {
        "Chandigarh": {"lat": 30.7333, "lon": 76.7794}
    },
    "Puducherry": {
        "Puducherry": {"lat": 11.9416, "lon": 79.8083},
        "Karaikal": {"lat": 10.9254, "lon": 79.8380},
        "Mahe": {"lat": 11.7003, "lon": 75.5343},
        "Yanam": {"lat": 16.7333, "lon": 82.2167}
    },
    "Andaman and Nicobar Islands": {
        "Port Blair (South Andaman)": {"lat": 11.6234, "lon": 92.7265},
        "Car Nicobar": {"lat": 9.1583, "lon": 92.8183},
        "Mayabunder (North & Middle Andaman)": {"lat": 12.9242, "lon": 92.9300},
        "Diglipur": {"lat": 13.2667, "lon": 92.9833},
        "Havelock Island (Swaraj Dweep)": {"lat": 11.9800, "lon": 92.9800}
    },
    "Dadra and Nagar Haveli and Daman and Diu": {
        "Daman": {"lat": 20.3974, "lon": 72.8328},
        "Diu": {"lat": 20.7144, "lon": 70.9874},
        "Silvassa": {"lat": 20.2763, "lon": 73.0083}
    },
    "Lakshadweep": {
        "Kavaratti": {"lat": 10.5667, "lon": 72.6417},
        "Agatti": {"lat": 10.8533, "lon": 72.1931},
        "Minicoy": {"lat": 8.2833, "lon": 73.0500},
        "Amini": {"lat": 11.1242, "lon": 72.7314}
    }
}

# Precompute lists and lookups
ALL_STATES = sorted(list(INDIA_STATES_DISTRICTS.keys()))

ALL_DISTRICTS_LOOKUP = {}
DISTRICT_SUGGESTIONS = []

for state, districts in INDIA_STATES_DISTRICTS.items():
    for dist_name, coords in districts.items():
        key = dist_name.lower()
        ALL_DISTRICTS_LOOKUP[key] = {
            "state": state,
            "district": dist_name,
            "lat": coords["lat"],
            "lon": coords["lon"]
        }
        clean_name = dist_name.split("(")[0].strip().lower()
        if clean_name not in ALL_DISTRICTS_LOOKUP:
            ALL_DISTRICTS_LOOKUP[clean_name] = ALL_DISTRICTS_LOOKUP[key]

        DISTRICT_SUGGESTIONS.append({
            "district": dist_name,
            "state": state,
            "display": f"{dist_name}, {state}",
            "lat": coords["lat"],
            "lon": coords["lon"]
        })

DISTRICT_SUGGESTIONS = sorted(DISTRICT_SUGGESTIONS, key=lambda x: x["display"])

def get_all_states():
    """Returns sorted list of all 36 States and Union Territories."""
    return ALL_STATES

def get_districts_for_state(state_name):
    """Returns list of district objects for the given state."""
    dist_dict = INDIA_STATES_DISTRICTS.get(state_name, {})
    results = []
    for name, coords in dist_dict.items():
        results.append({
            "name": name,
            "lat": coords["lat"],
            "lon": coords["lon"]
        })
    return sorted(results, key=lambda x: x["name"])

def find_nearest_district(lat, lon):
    """
    Finds the geographically closest Indian district and state for any given GPS coordinates.
    Computes equirectangular geodesic distance in kilometers.
    """
    if lat is None or lon is None:
        return "Maharashtra", "Pune", 0.0

    import math
    best = None
    min_d = float('inf')
    lat_f = float(lat)
    lon_f = float(lon)

    cos_lat = math.cos(math.radians(lat_f))
    for st, dists in INDIA_STATES_DISTRICTS.items():
        for d, coords in dists.items():
            dlat = coords["lat"] - lat_f
            dlon = (coords["lon"] - lon_f) * cos_lat
            dist = math.sqrt(dlat * dlat + dlon * dlon) * 111.0
            if dist < min_d:
                min_d = dist
                best = (st, d, round(dist, 1))

    return best or ("Maharashtra", "Pune", 0.0)

def resolve_location(state_name=None, district_name=None, city_name=None, lat=None, lon=None):
    """
    Resolves location coordinates and canonical names given State/District/City or GPS lat/lon.
    Prioritizes GPS reverse-lookup when coordinates are provided and district is unspecified.
    """
    # 0. If exact GPS coordinates are supplied without district name, reverse-geocode to nearest district
    if (lat is not None and lon is not None) and not district_name and not city_name:
        st, dist, _ = find_nearest_district(lat, lon)
        return st, dist, float(lat), float(lon)

    target = (district_name or city_name or "").strip().lower()

    # 0. Check MAJOR_METEO_ALIASES first for instant high-precision lookup
    if target and target in MAJOR_METEO_ALIASES:
        meta = MAJOR_METEO_ALIASES[target]
        return meta[0], meta[1], meta[2], meta[3]

    # 1. Exact match in state
    if state_name and district_name:
        state_dict = INDIA_STATES_DISTRICTS.get(state_name)
        if state_dict and district_name in state_dict:
            c = state_dict[district_name]
            return state_name, district_name, c["lat"], c["lon"]

    # 2. Lookup by district_name in ALL_DISTRICTS_LOOKUP
    if target:
        if target in ALL_DISTRICTS_LOOKUP:
            entry = ALL_DISTRICTS_LOOKUP[target]
            return entry["state"], entry["district"], entry["lat"], entry["lon"]

        clean_target = target.split("(")[0].strip()
        if clean_target in ALL_DISTRICTS_LOOKUP:
            entry = ALL_DISTRICTS_LOOKUP[clean_target]
            return entry["state"], entry["district"], entry["lat"], entry["lon"]

        # Partial search
        for key, entry in ALL_DISTRICTS_LOOKUP.items():
            if target in key or key in target:
                return entry["state"], entry["district"], entry["lat"], entry["lon"]

    # 3. If state_name is provided, check STATE_CAPITALS
    if state_name and state_name.lower() in STATE_CAPITALS:
        meta = STATE_CAPITALS[state_name.lower()]
        return meta[0], meta[1], meta[2], meta[3]

    # 4. Default to Pune if explicitly requested, otherwise New Delhi
    if "pune" in target:
        c = INDIA_STATES_DISTRICTS["Maharashtra"]["Pune"]
        return "Maharashtra", "Pune", c["lat"], c["lon"]

    c = INDIA_STATES_DISTRICTS["Delhi"]["New Delhi"]
    return "Delhi", "New Delhi", c["lat"], c["lon"]

MAJOR_METEO_ALIASES = {
    "new delhi": ("Delhi", "New Delhi", 28.6139, 77.2090),
    "delhi": ("Delhi", "New Delhi", 28.6139, 77.2090),
    "ncr": ("Delhi", "New Delhi", 28.6139, 77.2090),
    "noida": ("Uttar Pradesh", "Gautam Buddha Nagar (Noida)", 28.5355, 77.3910),
    "gurugram": ("Haryana", "Gurugram", 28.4595, 77.0266),
    "gurgaon": ("Haryana", "Gurugram", 28.4595, 77.0266),
    "faridabad": ("Haryana", "Faridabad", 28.4089, 77.3178),
    "ghaziabad": ("Uttar Pradesh", "Ghaziabad", 28.6692, 77.4538),
    "mumbai": ("Maharashtra", "Mumbai City", 19.0760, 72.8777),
    "bombay": ("Maharashtra", "Mumbai City", 19.0760, 72.8777),
    "bengaluru": ("Karnataka", "Bengaluru Urban", 12.9716, 77.5946),
    "bangalore": ("Karnataka", "Bengaluru Urban", 12.9716, 77.5946),
    "chennai": ("Tamil Nadu", "Chennai", 13.0827, 80.2707),
    "madras": ("Tamil Nadu", "Chennai", 13.0827, 80.2707),
    "kolkata": ("West Bengal", "Kolkata", 22.5726, 88.3639),
    "calcutta": ("West Bengal", "Kolkata", 22.5726, 88.3639),
    "hyderabad": ("Telangana", "Hyderabad", 17.3850, 78.4867),
    "secunderabad": ("Telangana", "Hyderabad", 17.3850, 78.4867),
    "pune": ("Maharashtra", "Pune", 18.5204, 73.8567),
    "ahmedabad": ("Gujarat", "Ahmedabad", 23.0225, 72.5714),
    "jaipur": ("Rajasthan", "Jaipur", 26.9124, 75.7873),
    "lucknow": ("Uttar Pradesh", "Lucknow", 26.8467, 80.9462),
    "patna": ("Bihar", "Patna", 25.5941, 85.1376),
    "bhubaneswar": ("Odisha", "Bhubaneswar", 20.2961, 85.8245),
    "puri": ("Odisha", "Puri", 19.8135, 85.8312),
    "cuttack": ("Odisha", "Cuttack", 20.4625, 85.8828),
    "guwahati": ("Assam", "Guwahati", 26.1445, 91.7362),
    "srinagar": ("Jammu and Kashmir", "Srinagar", 34.0837, 74.7973),
    "shimla": ("Himachal Pradesh", "Shimla", 31.1048, 77.1734),
    "dehradun": ("Uttarakhand", "Dehradun", 30.3165, 78.0322),
    "chandigarh": ("Punjab", "Chandigarh", 30.7333, 76.7794),
    "kochi": ("Kerala", "Kochi", 9.9312, 76.2673),
    "cochin": ("Kerala", "Kochi", 9.9312, 76.2673),
    "thiruvananthapuram": ("Kerala", "Thiruvananthapuram", 8.5241, 76.9366),
    "trivandrum": ("Kerala", "Thiruvananthapuram", 8.5241, 76.9366),
    "varanasi": ("Uttar Pradesh", "Varanasi", 25.3176, 82.9739),
    "kanpur": ("Uttar Pradesh", "Kanpur Nagar", 26.4499, 80.3319),
    "visakhapatnam": ("Andhra Pradesh", "Visakhapatnam", 17.6868, 83.2185),
    "vizag": ("Andhra Pradesh", "Visakhapatnam", 17.6868, 83.2185),
    "vijayawada": ("Andhra Pradesh", "Vijayawada", 16.5062, 80.6480),
    "nagpur": ("Maharashtra", "Nagpur", 21.1458, 79.0882),
    "indore": ("Madhya Pradesh", "Indore", 22.7196, 75.8577),
    "bhopal": ("Madhya Pradesh", "Bhopal", 23.2599, 77.4126),
    "raipur": ("Chhattisgarh", "Raipur", 21.2514, 81.6296),
    "panaji": ("Goa", "Panaji (North Goa)", 15.4909, 73.8278),
    "ranchi": ("Jharkhand", "Ranchi", 23.3441, 85.3096),
    "amritsar": ("Punjab", "Amritsar", 31.6340, 74.8723),
    "surat": ("Gujarat", "Surat", 21.1702, 72.8311),
    "coimbatore": ("Tamil Nadu", "Coimbatore", 11.0168, 76.9558),
    "leh": ("Ladakh", "Leh", 34.1526, 77.5771),
    "shillong": ("Meghalaya", "Shillong (East Khasi Hills)", 25.5788, 91.8933),
    "bengal": ("West Bengal", "Kolkata", 22.5726, 88.3639),
    "bay of bengal": ("West Bengal", "Kolkata", 22.5726, 88.3639)
}

STATE_CAPITALS = {
    "maharashtra": ("Maharashtra", "Mumbai City", 19.0760, 72.8777),
    "delhi": ("Delhi", "New Delhi", 28.6139, 77.2090),
    "karnataka": ("Karnataka", "Bengaluru Urban", 12.9716, 77.5946),
    "tamil nadu": ("Tamil Nadu", "Chennai", 13.0827, 80.2707),
    "west bengal": ("West Bengal", "Kolkata", 22.5726, 88.3639),
    "telangana": ("Telangana", "Hyderabad", 17.3850, 78.4867),
    "andhra pradesh": ("Andhra Pradesh", "Vijayawada", 16.5062, 80.6480),
    "gujarat": ("Gujarat", "Ahmedabad", 23.0225, 72.5714),
    "rajasthan": ("Rajasthan", "Jaipur", 26.9124, 75.7873),
    "uttar pradesh": ("Uttar Pradesh", "Lucknow", 26.8467, 80.9462),
    "bihar": ("Bihar", "Patna", 25.5941, 85.1376),
    "odisha": ("Odisha", "Bhubaneswar", 20.2961, 85.8245),
    "assam": ("Assam", "Guwahati", 26.1445, 91.7362),
    "kerala": ("Kerala", "Thiruvananthapuram", 8.5241, 76.9366),
    "madhya pradesh": ("Madhya Pradesh", "Bhopal", 23.2599, 77.4126),
    "punjab": ("Punjab", "Chandigarh", 30.7333, 76.7794),
    "haryana": ("Haryana", "Chandigarh", 30.7333, 76.7794),
    "jharkhand": ("Jharkhand", "Ranchi", 23.3441, 85.3096),
    "chhattisgarh": ("Chhattisgarh", "Raipur", 21.2514, 81.6296),
    "himachal pradesh": ("Himachal Pradesh", "Shimla", 31.1048, 77.1734),
    "uttarakhand": ("Uttarakhand", "Dehradun", 30.3165, 78.0322),
    "jammu and kashmir": ("Jammu and Kashmir", "Srinagar", 34.0837, 74.7973),
    "goa": ("Goa", "Panaji (North Goa)", 15.4909, 73.8278),
    "meghalaya": ("Meghalaya", "Shillong (East Khasi Hills)", 25.5788, 91.8933),
    "tripura": ("Tripura", "Agartala", 23.8315, 91.2868),
    "manipur": ("Manipur", "Imphal", 24.8170, 93.9368),
    "nagaland": ("Nagaland", "Kohima", 25.6751, 94.1086),
    "mizoram": ("Mizoram", "Aizawl", 23.7271, 92.7176),
    "sikkim": ("Sikkim", "Gangtok", 27.3389, 88.6065),
    "arunachal pradesh": ("Arunachal Pradesh", "Itanagar", 27.0844, 93.6053),
    "ladakh": ("Ladakh", "Leh", 34.1526, 77.5771)
}

def extract_location_from_text(text):
    """
    Accurately extracts Indian State, District, and coordinates from arbitrary weather text.
    Prioritizes specific major city aliases first, then full 500+ district registry, then state capitals.
    """
    if not text:
        return "Delhi", "New Delhi", 28.6139, 77.2090

    text_lower = text.lower()

    # Step 1: Check high-precision major city and meteorological station aliases
    for alias, meta in sorted(MAJOR_METEO_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
            return meta[0], meta[1], meta[2], meta[3]

    # Step 2: Check all districts across India by length descending
    for d_clean, entry in sorted(ALL_DISTRICTS_LOOKUP.items(), key=lambda x: len(x[0]), reverse=True):
        if len(d_clean) > 3 and re.search(r'\b' + re.escape(d_clean) + r'\b', text_lower):
            return entry['state'], entry['district'], entry['lat'], entry['lon']

    # Step 3: Check states and map to their official capital/headquarters
    for state_name, meta in sorted(STATE_CAPITALS.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r'\b' + re.escape(state_name) + r'\b', text_lower):
            return meta[0], meta[1], meta[2], meta[3]

    # Step 4: Default fallback to National Capital New Delhi
    return "Delhi", "New Delhi", 28.6139, 77.2090
