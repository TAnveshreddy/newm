// Runtime i18n dictionary — English, Hindi, Telugu, Marathi, Tamil.
// Keys mirror the web/Angular app. Missing keys fall back to English, then key.

class LangDef {
  final String code;
  final String label; // native name
  final String english;
  const LangDef(this.code, this.label, this.english);
}

const List<LangDef> kLanguages = [
  LangDef('en', 'English', 'English'),
  LangDef('hi', 'हिन्दी', 'Hindi'),
  LangDef('te', 'తెలుగు', 'Telugu'),
  LangDef('mr', 'मराठी', 'Marathi'),
  LangDef('ta', 'தமிழ்', 'Tamil'),
];

const Map<String, String> _en = {
  'lang.choose': 'Choose your language',
  'lang.chooseSub': 'Select the language you would like to use. You can change it later in Settings.',
  'lang.continue': 'Continue', 'lang.label': 'Language',
  'common.save': 'Save', 'common.cancel': 'Cancel', 'common.delete': 'Delete',
  'common.logout': 'Sign out', 'common.total': 'Total',
  'nav.dashboard': 'Dashboard', 'nav.billing': 'Billing', 'nav.inventory': 'Inventory',
  'nav.khata': 'Khata', 'nav.more': 'More', 'nav.admin': 'Admin Console',
  'login.sub': 'Billing · Inventory · Khata — synced across your devices',
  'login.google': 'Continue with Google', 'login.or': 'OR', 'login.mobile': 'Mobile Number',
  'login.getOtp': 'Get OTP', 'login.verify': 'Verify & Login', 'login.enterOtp': 'Enter OTP',
  'login.change': '← Change number',
  'dash.title': 'Dashboard', 'dash.overview': 'Overview of your business',
  'dash.todaySales': "Today's Sales", 'dash.todayProfit': "Today's Profit",
  'dash.billsToday': 'Bills Today', 'dash.lowStock': 'Low Stock',
  'dash.toCollect': 'To Collect', 'dash.toPay': 'To Pay',
  'dash.lowStockItems': 'Low Stock Items', 'dash.recentTxns': 'Recent Transactions',
  'dash.wellStocked': '🎉 All items are well stocked.', 'dash.noTxns': 'No transactions yet.',
  'bill.title': 'Billing', 'bill.customer': 'Customer (optional)', 'bill.contact': 'Contact Number',
  'bill.payMode': 'Payment Mode', 'bill.searchAdd': 'Search product to add',
  'bill.startBill': 'Add products to start the bill.', 'bill.saveBill': 'Save Bill',
  'bill.savePrint': 'Save & Print', 'bill.clear': 'Clear', 'bill.total': 'Total',
  'inv.title': 'Inventory', 'inv.addProduct': 'Add Product', 'inv.search': 'Search products…',
  'khata.title': 'Khata', 'khata.customers': 'Customers', 'khata.suppliers': 'Suppliers',
  'khata.addParty': 'Add Party',
  'more.signedIn': 'Signed in', 'set.language': 'Language',
};

const Map<String, String> _hi = {
  'lang.choose': 'अपनी भाषा चुनें',
  'lang.chooseSub': 'आप जिस भाषा का उपयोग करना चाहते हैं उसे चुनें। इसे बाद में सेटिंग्स में बदला जा सकता है।',
  'lang.continue': 'जारी रखें', 'lang.label': 'भाषा',
  'common.save': 'सहेजें', 'common.cancel': 'रद्द करें', 'common.delete': 'हटाएं',
  'common.logout': 'साइन आउट', 'common.total': 'कुल',
  'nav.dashboard': 'डैशबोर्ड', 'nav.billing': 'बिलिंग', 'nav.inventory': 'इन्वेंटरी',
  'nav.khata': 'खाता', 'nav.more': 'और', 'nav.admin': 'एडमिन कंसोल',
  'login.sub': 'बिलिंग · इन्वेंटरी · खाता — आपके सभी डिवाइस पर सिंक',
  'login.google': 'Google से जारी रखें', 'login.or': 'या', 'login.mobile': 'मोबाइल नंबर',
  'login.getOtp': 'OTP प्राप्त करें', 'login.verify': 'सत्यापित करें और लॉगिन करें', 'login.enterOtp': 'OTP दर्ज करें',
  'login.change': '← नंबर बदलें',
  'dash.title': 'डैशबोर्ड', 'dash.overview': 'आपके व्यवसाय का अवलोकन',
  'dash.todaySales': 'आज की बिक्री', 'dash.todayProfit': 'आज का लाभ',
  'dash.billsToday': 'आज के बिल', 'dash.lowStock': 'कम स्टॉक',
  'dash.toCollect': 'प्राप्य', 'dash.toPay': 'देय',
  'dash.lowStockItems': 'कम स्टॉक वाली वस्तुएं', 'dash.recentTxns': 'हाल के लेन-देन',
  'dash.wellStocked': '🎉 सभी वस्तुएं पर्याप्त स्टॉक में हैं।', 'dash.noTxns': 'अभी तक कोई लेन-देन नहीं।',
  'bill.title': 'बिलिंग', 'bill.customer': 'ग्राहक (वैकल्पिक)', 'bill.contact': 'संपर्क नंबर',
  'bill.payMode': 'भुगतान का तरीका', 'bill.searchAdd': 'जोड़ने के लिए उत्पाद खोजें',
  'bill.startBill': 'बिल शुरू करने के लिए उत्पाद जोड़ें।', 'bill.saveBill': 'बिल सहेजें',
  'bill.savePrint': 'सहेजें और प्रिंट करें', 'bill.clear': 'साफ़ करें', 'bill.total': 'कुल',
  'inv.title': 'इन्वेंटरी', 'inv.addProduct': 'उत्पाद जोड़ें', 'inv.search': 'उत्पाद खोजें…',
  'khata.title': 'खाता', 'khata.customers': 'ग्राहक', 'khata.suppliers': 'आपूर्तिकर्ता',
  'khata.addParty': 'पार्टी जोड़ें',
  'more.signedIn': 'साइन इन है', 'set.language': 'भाषा',
};

const Map<String, String> _te = {
  'lang.choose': 'మీ భాషను ఎంచుకోండి',
  'lang.chooseSub': 'మీరు ఉపయోగించాలనుకుంటున్న భాషను ఎంచుకోండి. దీన్ని తర్వాత సెట్టింగ్‌లలో మార్చవచ్చు.',
  'lang.continue': 'కొనసాగించు', 'lang.label': 'భాష',
  'common.save': 'సేవ్', 'common.cancel': 'రద్దు', 'common.delete': 'తొలగించు',
  'common.logout': 'సైన్ అవుట్', 'common.total': 'మొత్తం',
  'nav.dashboard': 'డాష్‌బోర్డ్', 'nav.billing': 'బిల్లింగ్', 'nav.inventory': 'ఇన్వెంటరీ',
  'nav.khata': 'ఖాతా', 'nav.more': 'మరిన్ని', 'nav.admin': 'అడ్మిన్ కన్సోల్',
  'login.sub': 'బిల్లింగ్ · ఇన్వెంటరీ · ఖాతా — మీ అన్ని పరికరాలలో సింక్',
  'login.google': 'Googleతో కొనసాగించండి', 'login.or': 'లేదా', 'login.mobile': 'మొబైల్ నంబర్',
  'login.getOtp': 'OTP పొందండి', 'login.verify': 'ధృవీకరించి లాగిన్', 'login.enterOtp': 'OTP నమోదు చేయండి',
  'login.change': '← నంబర్ మార్చండి',
  'dash.title': 'డాష్‌బోర్డ్', 'dash.overview': 'మీ వ్యాపారం యొక్క అవలోకనం',
  'dash.todaySales': 'నేటి అమ్మకాలు', 'dash.todayProfit': 'నేటి లాభం',
  'dash.billsToday': 'నేటి బిల్లులు', 'dash.lowStock': 'తక్కువ స్టాక్',
  'dash.toCollect': 'వసూలు చేయాలి', 'dash.toPay': 'చెల్లించాలి',
  'dash.lowStockItems': 'తక్కువ స్టాక్ వస్తువులు', 'dash.recentTxns': 'ఇటీవలి లావాదేవీలు',
  'dash.wellStocked': '🎉 అన్ని వస్తువులు తగినంత స్టాక్‌లో ఉన్నాయి.', 'dash.noTxns': 'ఇంకా లావాదేవీలు లేవు.',
  'bill.title': 'బిల్లింగ్', 'bill.customer': 'కస్టమర్ (ఐచ్ఛికం)', 'bill.contact': 'సంప్రదింపు నంబర్',
  'bill.payMode': 'చెల్లింపు విధానం', 'bill.searchAdd': 'జోడించడానికి ఉత్పత్తిని వెతకండి',
  'bill.startBill': 'బిల్లు ప్రారంభించడానికి ఉత్పత్తులను జోడించండి.', 'bill.saveBill': 'బిల్లు సేవ్ చేయి',
  'bill.savePrint': 'సేవ్ & ప్రింట్', 'bill.clear': 'క్లియర్', 'bill.total': 'మొత్తం',
  'inv.title': 'ఇన్వెంటరీ', 'inv.addProduct': 'ఉత్పత్తిని జోడించు', 'inv.search': 'ఉత్పత్తులను వెతకండి…',
  'khata.title': 'ఖాతా', 'khata.customers': 'కస్టమర్లు', 'khata.suppliers': 'సరఫరాదారులు',
  'khata.addParty': 'పార్టీని జోడించు',
  'more.signedIn': 'సైన్ ఇన్ అయ్యారు', 'set.language': 'భాష',
};

const Map<String, String> _mr = {
  'lang.choose': 'तुमची भाषा निवडा',
  'lang.chooseSub': 'तुम्हाला वापरायची भाषा निवडा. ती नंतर सेटिंग्जमध्ये बदलता येईल.',
  'lang.continue': 'सुरू ठेवा', 'lang.label': 'भाषा',
  'common.save': 'जतन करा', 'common.cancel': 'रद्द करा', 'common.delete': 'हटवा',
  'common.logout': 'साइन आउट', 'common.total': 'एकूण',
  'nav.dashboard': 'डॅशबोर्ड', 'nav.billing': 'बिलिंग', 'nav.inventory': 'इन्व्हेंटरी',
  'nav.khata': 'खाते', 'nav.more': 'अधिक', 'nav.admin': 'ॲडमिन कन्सोल',
  'login.sub': 'बिलिंग · इन्व्हेंटरी · खाते — तुमच्या सर्व डिव्हाइसवर सिंक',
  'login.google': 'Google ने सुरू ठेवा', 'login.or': 'किंवा', 'login.mobile': 'मोबाइल नंबर',
  'login.getOtp': 'OTP मिळवा', 'login.verify': 'पडताळा आणि लॉगिन', 'login.enterOtp': 'OTP प्रविष्ट करा',
  'login.change': '← नंबर बदला',
  'dash.title': 'डॅशबोर्ड', 'dash.overview': 'तुमच्या व्यवसायाचा आढावा',
  'dash.todaySales': 'आजची विक्री', 'dash.todayProfit': 'आजचा नफा',
  'dash.billsToday': 'आजची बिले', 'dash.lowStock': 'कमी स्टॉक',
  'dash.toCollect': 'येणे', 'dash.toPay': 'देणे',
  'dash.lowStockItems': 'कमी स्टॉक असलेल्या वस्तू', 'dash.recentTxns': 'अलीकडील व्यवहार',
  'dash.wellStocked': '🎉 सर्व वस्तू पुरेशा स्टॉकमध्ये आहेत.', 'dash.noTxns': 'अद्याप कोणतेही व्यवहार नाहीत.',
  'bill.title': 'बिलिंग', 'bill.customer': 'ग्राहक (पर्यायी)', 'bill.contact': 'संपर्क क्रमांक',
  'bill.payMode': 'पेमेंट पद्धत', 'bill.searchAdd': 'जोडण्यासाठी उत्पादन शोधा',
  'bill.startBill': 'बिल सुरू करण्यासाठी उत्पादने जोडा.', 'bill.saveBill': 'बिल जतन करा',
  'bill.savePrint': 'जतन करा आणि प्रिंट करा', 'bill.clear': 'साफ करा', 'bill.total': 'एकूण',
  'inv.title': 'इन्व्हेंटरी', 'inv.addProduct': 'उत्पादन जोडा', 'inv.search': 'उत्पादने शोधा…',
  'khata.title': 'खाते', 'khata.customers': 'ग्राहक', 'khata.suppliers': 'पुरवठादार',
  'khata.addParty': 'पार्टी जोडा',
  'more.signedIn': 'साइन इन आहे', 'set.language': 'भाषा',
};

const Map<String, String> _ta = {
  'lang.choose': 'உங்கள் மொழியைத் தேர்ந்தெடுக்கவும்',
  'lang.chooseSub': 'நீங்கள் பயன்படுத்த விரும்பும் மொழியைத் தேர்ந்தெடுக்கவும். பின்னர் அமைப்புகளில் மாற்றலாம்.',
  'lang.continue': 'தொடரவும்', 'lang.label': 'மொழி',
  'common.save': 'சேமி', 'common.cancel': 'ரத்து', 'common.delete': 'நீக்கு',
  'common.logout': 'வெளியேறு', 'common.total': 'மொத்தம்',
  'nav.dashboard': 'டாஷ்போர்டு', 'nav.billing': 'பில்லிங்', 'nav.inventory': 'சரக்கு',
  'nav.khata': 'கணக்கு', 'nav.more': 'மேலும்', 'nav.admin': 'நிர்வாக பலகை',
  'login.sub': 'பில்லிங் · சரக்கு · கணக்கு — உங்கள் அனைத்து சாதனங்களிலும் ஒத்திசைவு',
  'login.google': 'Google உடன் தொடரவும்', 'login.or': 'அல்லது', 'login.mobile': 'மொபைல் எண்',
  'login.getOtp': 'OTP பெறவும்', 'login.verify': 'சரிபார்த்து உள்நுழை', 'login.enterOtp': 'OTP ஐ உள்ளிடவும்',
  'login.change': '← எண்ணை மாற்று',
  'dash.title': 'டாஷ்போர்டு', 'dash.overview': 'உங்கள் வணிகத்தின் மேலோட்டம்',
  'dash.todaySales': 'இன்றைய விற்பனை', 'dash.todayProfit': 'இன்றைய லாபம்',
  'dash.billsToday': 'இன்றைய பில்கள்', 'dash.lowStock': 'குறைந்த சரக்கு',
  'dash.toCollect': 'வசூலிக்க', 'dash.toPay': 'செலுத்த',
  'dash.lowStockItems': 'குறைந்த சரக்கு பொருட்கள்', 'dash.recentTxns': 'சமீபத்திய பரிவர்த்தனைகள்',
  'dash.wellStocked': '🎉 அனைத்து பொருட்களும் போதுமான சரக்கில் உள்ளன.', 'dash.noTxns': 'இதுவரை பரிவர்த்தனைகள் இல்லை.',
  'bill.title': 'பில்லிங்', 'bill.customer': 'வாடிக்கையாளர் (விருப்பம்)', 'bill.contact': 'தொடர்பு எண்',
  'bill.payMode': 'கட்டண முறை', 'bill.searchAdd': 'சேர்க்க பொருளைத் தேடு',
  'bill.startBill': 'பில்லைத் தொடங்க பொருட்களைச் சேர்க்கவும்.', 'bill.saveBill': 'பில்லைச் சேமி',
  'bill.savePrint': 'சேமித்து அச்சிடு', 'bill.clear': 'அழி', 'bill.total': 'மொத்தம்',
  'inv.title': 'சரக்கு', 'inv.addProduct': 'பொருள் சேர்', 'inv.search': 'பொருட்களைத் தேடு…',
  'khata.title': 'கணக்கு', 'khata.customers': 'வாடிக்கையாளர்கள்', 'khata.suppliers': 'சப்ளையர்கள்',
  'khata.addParty': 'கட்சியைச் சேர்',
  'more.signedIn': 'உள்நுழைந்துள்ளீர்கள்', 'set.language': 'மொழி',
};

const Map<String, Map<String, String>> kTranslations = {
  'en': _en, 'hi': _hi, 'te': _te, 'mr': _mr, 'ta': _ta,
};

String translate(String lang, String key) =>
    kTranslations[lang]?[key] ?? _en[key] ?? key;
