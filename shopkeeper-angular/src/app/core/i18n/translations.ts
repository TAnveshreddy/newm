/**
 * Runtime i18n dictionary. Five languages; keys are dot-namespaced. Add a new
 * string by adding its key to every language map below and using `| t` in a
 * template. Missing keys fall back to English, then to the key itself.
 */
export type Lang = 'en' | 'hi' | 'te' | 'mr' | 'ta';

export interface LangDef { code: Lang; label: string; english: string; }

export const LANGUAGES: LangDef[] = [
  { code: 'en', label: 'English', english: 'English' },
  { code: 'hi', label: 'हिन्दी', english: 'Hindi' },
  { code: 'te', label: 'తెలుగు', english: 'Telugu' },
  { code: 'mr', label: 'मराठी', english: 'Marathi' },
  { code: 'ta', label: 'தமிழ்', english: 'Tamil' },
];

type Dict = Record<string, string>;

const en: Dict = {
  'lang.choose': 'Choose your language',
  'lang.chooseSub': 'Select the language you would like to use. You can change it later in Settings.',
  'lang.continue': 'Continue',
  'lang.label': 'Language',

  'common.save': 'Save', 'common.cancel': 'Cancel', 'common.delete': 'Delete',
  'common.edit': 'Edit', 'common.search': 'Search', 'common.logout': 'Log out',
  'common.viewAll': 'View all', 'common.total': 'Total', 'common.subtotal': 'Subtotal',
  'common.gst': 'GST', 'common.add': 'Add',

  'nav.dashboard': 'Dashboard', 'nav.billing': 'Billing', 'nav.inventory': 'Inventory',
  'nav.khata': 'Khata', 'nav.reports': 'Reports', 'nav.settings': 'Settings', 'nav.admin': 'Admin',

  'login.sub': 'Billing · Inventory · Khata — synced across your devices',
  'login.google': 'Continue with Google', 'login.or': 'OR', 'login.mobile': 'Mobile Number',
  'login.getOtp': 'Get OTP', 'login.verify': 'Verify & Login', 'login.enterOtp': 'Enter OTP',
  'login.change': '← Change number', 'login.codeSent': 'Code sent to',
  'login.smsNote': 'A one-time code is sent by SMS to verify your number.',

  'dash.overview': 'Overview of your business', 'dash.todaySales': "Today's Sales",
  'dash.todayProfit': "Today's Profit", 'dash.billsToday': 'Bills Created Today',
  'dash.lowStock': 'Low Stock Items', 'dash.toCollect': 'To Collect', 'dash.toPay': 'To Pay',
  'dash.vsYesterday': 'vs yesterday', 'dash.viewItems': 'View items', 'dash.viewDetails': 'View details',
  'dash.salesOverview': 'Sales Overview', 'dash.businessSummary': 'Business Summary',
  'dash.totalSales': 'Total Sales', 'dash.totalProfit': 'Total Profit',
  'dash.totalPurchases': 'Total Purchases', 'dash.totalExpenses': 'Total Expenses',
  'dash.viewReport': 'View full report', 'dash.recentTxns': 'Recent Transactions',
  'dash.viewAllItems': 'View all items', 'dash.wellStocked': 'All items are well stocked.',
  'dash.noTxns': 'No transactions yet.', 'dash.thisMonth': 'This Month',
  'dash.lastMonth': 'Last Month', 'dash.thisYear': 'This Year', 'dash.newBill': 'New Bill',
  'dash.needAttention': 'need attention', 'dash.available': 'Available', 'dash.reorder': 'Reorder',
  'dash.status': 'Status', 'dash.item': 'Item', 'dash.category': 'Category',

  'bill.title': 'Billing', 'bill.createInvoice': 'Create a sale invoice',
  'bill.customer': 'Customer Name', 'bill.cashSale': 'Cash sale (optional)',
  'bill.contact': 'Contact Number', 'bill.payMode': 'Payment Mode',
  'bill.scan': 'Scan Barcode', 'bill.scanHint': 'Click here, then scan — item is added automatically',
  'bill.searchProduct': 'Search product (quick add)', 'bill.searchHint': 'Type to search, click a product to add…',
  'bill.category': 'Category', 'bill.allCategories': 'All Categories', 'bill.item': 'Item',
  'bill.selectItem': '— select item —', 'bill.brand': 'Brand', 'bill.brandHint': 'Auto-fills from item',
  'bill.desc': 'Product Description', 'bill.descHint': 'Prints on invoice', 'bill.addToBill': 'Add to Bill',
  'bill.product': 'Product', 'bill.qty': 'Qty', 'bill.rate': 'Rate', 'bill.amountPaid': 'Amount Paid',
  'bill.saveBill': 'Save Bill', 'bill.savePrint': 'Save & Print', 'bill.clearBill': 'Clear Bill',
  'bill.startBill': 'Scan or add products to start the bill.', 'bill.noMatch': 'No matching products.',

  'inv.title': 'Inventory', 'inv.addProduct': 'Add Product', 'inv.searchProducts': 'Search products…',
  'inv.scanBarcode': 'Scan barcode…', 'inv.stockValue': 'Stock Value (at cost)', 'inv.labels': 'Labels',

  'khata.title': 'Khata', 'khata.customers': 'Customers', 'khata.suppliers': 'Suppliers',
  'khata.addParty': 'Add Party',

  'set.title': 'Settings', 'set.businessProfile': 'Business Profile (shown on invoices)',
  'set.preferences': 'Preferences', 'set.account': 'Account & Subscription', 'set.login': 'Login',
  'set.saveProfile': 'Save Profile', 'set.gstEnable': 'Enable GST on transactions',
  'set.darkTheme': 'Dark theme', 'set.businessName': 'Business Name',
};

const hi: Dict = {
  'lang.choose': 'अपनी भाषा चुनें',
  'lang.chooseSub': 'आप जिस भाषा का उपयोग करना चाहते हैं उसे चुनें। इसे बाद में सेटिंग्स में बदला जा सकता है।',
  'lang.continue': 'जारी रखें', 'lang.label': 'भाषा',

  'common.save': 'सहेजें', 'common.cancel': 'रद्द करें', 'common.delete': 'हटाएं',
  'common.edit': 'संपादित करें', 'common.search': 'खोजें', 'common.logout': 'लॉग आउट',
  'common.viewAll': 'सभी देखें', 'common.total': 'कुल', 'common.subtotal': 'उप-योग',
  'common.gst': 'जीएसटी', 'common.add': 'जोड़ें',

  'nav.dashboard': 'डैशबोर्ड', 'nav.billing': 'बिलिंग', 'nav.inventory': 'इन्वेंटरी',
  'nav.khata': 'खाता', 'nav.reports': 'रिपोर्ट', 'nav.settings': 'सेटिंग्स', 'nav.admin': 'एडमिन',

  'login.sub': 'बिलिंग · इन्वेंटरी · खाता — आपके सभी डिवाइस पर सिंक',
  'login.google': 'Google से जारी रखें', 'login.or': 'या', 'login.mobile': 'मोबाइल नंबर',
  'login.getOtp': 'OTP प्राप्त करें', 'login.verify': 'सत्यापित करें और लॉगिन करें', 'login.enterOtp': 'OTP दर्ज करें',
  'login.change': '← नंबर बदलें', 'login.codeSent': 'कोड भेजा गया',
  'login.smsNote': 'आपके नंबर को सत्यापित करने के लिए SMS द्वारा एक बार का कोड भेजा जाता है।',

  'dash.overview': 'आपके व्यवसाय का अवलोकन', 'dash.todaySales': 'आज की बिक्री',
  'dash.todayProfit': 'आज का लाभ', 'dash.billsToday': 'आज बनाए गए बिल',
  'dash.lowStock': 'कम स्टॉक वाली वस्तुएं', 'dash.toCollect': 'प्राप्य', 'dash.toPay': 'देय',
  'dash.vsYesterday': 'कल की तुलना में', 'dash.viewItems': 'आइटम देखें', 'dash.viewDetails': 'विवरण देखें',
  'dash.salesOverview': 'बिक्री अवलोकन', 'dash.businessSummary': 'व्यवसाय सारांश',
  'dash.totalSales': 'कुल बिक्री', 'dash.totalProfit': 'कुल लाभ',
  'dash.totalPurchases': 'कुल खरीद', 'dash.totalExpenses': 'कुल व्यय',
  'dash.viewReport': 'पूरी रिपोर्ट देखें', 'dash.recentTxns': 'हाल के लेन-देन',
  'dash.viewAllItems': 'सभी आइटम देखें', 'dash.wellStocked': 'सभी वस्तुएं पर्याप्त स्टॉक में हैं।',
  'dash.noTxns': 'अभी तक कोई लेन-देन नहीं।', 'dash.thisMonth': 'इस महीने',
  'dash.lastMonth': 'पिछले महीने', 'dash.thisYear': 'इस साल', 'dash.newBill': 'नया बिल',
  'dash.needAttention': 'ध्यान चाहिए', 'dash.available': 'उपलब्ध', 'dash.reorder': 'पुनः ऑर्डर',
  'dash.status': 'स्थिति', 'dash.item': 'वस्तु', 'dash.category': 'श्रेणी',

  'bill.title': 'बिलिंग', 'bill.createInvoice': 'बिक्री चालान बनाएं',
  'bill.customer': 'ग्राहक का नाम', 'bill.cashSale': 'नकद बिक्री (वैकल्पिक)',
  'bill.contact': 'संपर्क नंबर', 'bill.payMode': 'भुगतान का तरीका',
  'bill.scan': 'बारकोड स्कैन करें', 'bill.scanHint': 'यहां क्लिक करें, फिर स्कैन करें — आइटम स्वतः जुड़ जाता है',
  'bill.searchProduct': 'उत्पाद खोजें (त्वरित जोड़ें)', 'bill.searchHint': 'खोजने के लिए टाइप करें, जोड़ने के लिए उत्पाद पर क्लिक करें…',
  'bill.category': 'श्रेणी', 'bill.allCategories': 'सभी श्रेणियां', 'bill.item': 'आइटम',
  'bill.selectItem': '— आइटम चुनें —', 'bill.brand': 'ब्रांड', 'bill.brandHint': 'आइटम से स्वतः भरता है',
  'bill.desc': 'उत्पाद विवरण', 'bill.descHint': 'चालान पर प्रिंट होता है', 'bill.addToBill': 'बिल में जोड़ें',
  'bill.product': 'उत्पाद', 'bill.qty': 'मात्रा', 'bill.rate': 'दर', 'bill.amountPaid': 'भुगतान की गई राशि',
  'bill.saveBill': 'बिल सहेजें', 'bill.savePrint': 'सहेजें और प्रिंट करें', 'bill.clearBill': 'बिल साफ़ करें',
  'bill.startBill': 'बिल शुरू करने के लिए उत्पाद स्कैन करें या जोड़ें।', 'bill.noMatch': 'कोई मिलता-जुलता उत्पाद नहीं।',

  'inv.title': 'इन्वेंटरी', 'inv.addProduct': 'उत्पाद जोड़ें', 'inv.searchProducts': 'उत्पाद खोजें…',
  'inv.scanBarcode': 'बारकोड स्कैन करें…', 'inv.stockValue': 'स्टॉक मूल्य (लागत पर)', 'inv.labels': 'लेबल',

  'khata.title': 'खाता', 'khata.customers': 'ग्राहक', 'khata.suppliers': 'आपूर्तिकर्ता', 'khata.addParty': 'पार्टी जोड़ें',

  'set.title': 'सेटिंग्स', 'set.businessProfile': 'व्यवसाय प्रोफ़ाइल (चालान पर दिखता है)',
  'set.preferences': 'प्राथमिकताएं', 'set.account': 'खाता और सदस्यता', 'set.login': 'लॉगिन',
  'set.saveProfile': 'प्रोफ़ाइल सहेजें', 'set.gstEnable': 'लेन-देन पर जीएसटी सक्षम करें',
  'set.darkTheme': 'डार्क थीम', 'set.businessName': 'व्यवसाय का नाम',
};

const te: Dict = {
  'lang.choose': 'మీ భాషను ఎంచుకోండి',
  'lang.chooseSub': 'మీరు ఉపయోగించాలనుకుంటున్న భాషను ఎంచుకోండి. దీన్ని తర్వాత సెట్టింగ్‌లలో మార్చవచ్చు.',
  'lang.continue': 'కొనసాగించు', 'lang.label': 'భాష',

  'common.save': 'సేవ్', 'common.cancel': 'రద్దు', 'common.delete': 'తొలగించు',
  'common.edit': 'సవరించు', 'common.search': 'వెతుకు', 'common.logout': 'లాగ్ అవుట్',
  'common.viewAll': 'అన్నీ చూడండి', 'common.total': 'మొత్తం', 'common.subtotal': 'సబ్‌టోటల్',
  'common.gst': 'జీఎస్టీ', 'common.add': 'జోడించు',

  'nav.dashboard': 'డాష్‌బోర్డ్', 'nav.billing': 'బిల్లింగ్', 'nav.inventory': 'ఇన్వెంటరీ',
  'nav.khata': 'ఖాతా', 'nav.reports': 'నివేదికలు', 'nav.settings': 'సెట్టింగ్‌లు', 'nav.admin': 'అడ్మిన్',

  'login.sub': 'బిల్లింగ్ · ఇన్వెంటరీ · ఖాతా — మీ అన్ని పరికరాలలో సింక్',
  'login.google': 'Googleతో కొనసాగించండి', 'login.or': 'లేదా', 'login.mobile': 'మొబైల్ నంబర్',
  'login.getOtp': 'OTP పొందండి', 'login.verify': 'ధృవీకరించి లాగిన్ చేయండి', 'login.enterOtp': 'OTP నమోదు చేయండి',
  'login.change': '← నంబర్ మార్చండి', 'login.codeSent': 'కోడ్ పంపబడింది',
  'login.smsNote': 'మీ నంబర్‌ను ధృవీకరించడానికి SMS ద్వారా వన్-టైమ్ కోడ్ పంపబడుతుంది.',

  'dash.overview': 'మీ వ్యాపారం యొక్క అవలోకనం', 'dash.todaySales': 'నేటి అమ్మకాలు',
  'dash.todayProfit': 'నేటి లాభం', 'dash.billsToday': 'నేడు సృష్టించిన బిల్లులు',
  'dash.lowStock': 'తక్కువ స్టాక్ వస్తువులు', 'dash.toCollect': 'వసూలు చేయాలి', 'dash.toPay': 'చెల్లించాలి',
  'dash.vsYesterday': 'నిన్నటితో పోలిస్తే', 'dash.viewItems': 'వస్తువులు చూడండి', 'dash.viewDetails': 'వివరాలు చూడండి',
  'dash.salesOverview': 'అమ్మకాల అవలోకనం', 'dash.businessSummary': 'వ్యాపార సారాంశం',
  'dash.totalSales': 'మొత్తం అమ్మకాలు', 'dash.totalProfit': 'మొత్తం లాభం',
  'dash.totalPurchases': 'మొత్తం కొనుగోళ్లు', 'dash.totalExpenses': 'మొత్తం ఖర్చులు',
  'dash.viewReport': 'పూర్తి నివేదిక చూడండి', 'dash.recentTxns': 'ఇటీవలి లావాదేవీలు',
  'dash.viewAllItems': 'అన్ని వస్తువులు చూడండి', 'dash.wellStocked': 'అన్ని వస్తువులు తగినంత స్టాక్‌లో ఉన్నాయి.',
  'dash.noTxns': 'ఇంకా లావాదేవీలు లేవు.', 'dash.thisMonth': 'ఈ నెల',
  'dash.lastMonth': 'గత నెల', 'dash.thisYear': 'ఈ సంవత్సరం', 'dash.newBill': 'కొత్త బిల్లు',
  'dash.needAttention': 'శ్రద్ధ అవసరం', 'dash.available': 'అందుబాటులో', 'dash.reorder': 'రీఆర్డర్',
  'dash.status': 'స్థితి', 'dash.item': 'వస్తువు', 'dash.category': 'వర్గం',

  'bill.title': 'బిల్లింగ్', 'bill.createInvoice': 'అమ్మకపు ఇన్వాయిస్ సృష్టించండి',
  'bill.customer': 'కస్టమర్ పేరు', 'bill.cashSale': 'నగదు అమ్మకం (ఐచ్ఛికం)',
  'bill.contact': 'సంప్రదింపు నంబర్', 'bill.payMode': 'చెల్లింపు విధానం',
  'bill.scan': 'బార్‌కోడ్ స్కాన్', 'bill.scanHint': 'ఇక్కడ క్లిక్ చేసి స్కాన్ చేయండి — వస్తువు స్వయంచాలకంగా జోడించబడుతుంది',
  'bill.searchProduct': 'ఉత్పత్తిని వెతకండి (త్వరిత జోడింపు)', 'bill.searchHint': 'వెతకడానికి టైప్ చేయండి, జోడించడానికి ఉత్పత్తిపై క్లిక్ చేయండి…',
  'bill.category': 'వర్గం', 'bill.allCategories': 'అన్ని వర్గాలు', 'bill.item': 'వస్తువు',
  'bill.selectItem': '— వస్తువును ఎంచుకోండి —', 'bill.brand': 'బ్రాండ్', 'bill.brandHint': 'వస్తువు నుండి స్వయంచాలకంగా నింపుతుంది',
  'bill.desc': 'ఉత్పత్తి వివరణ', 'bill.descHint': 'ఇన్వాయిస్‌పై ప్రింట్ అవుతుంది', 'bill.addToBill': 'బిల్లుకు జోడించు',
  'bill.product': 'ఉత్పత్తి', 'bill.qty': 'పరిమాణం', 'bill.rate': 'ధర', 'bill.amountPaid': 'చెల్లించిన మొత్తం',
  'bill.saveBill': 'బిల్లు సేవ్ చేయి', 'bill.savePrint': 'సేవ్ & ప్రింట్', 'bill.clearBill': 'బిల్లు క్లియర్',
  'bill.startBill': 'బిల్లు ప్రారంభించడానికి ఉత్పత్తులను స్కాన్ చేయండి లేదా జోడించండి.', 'bill.noMatch': 'సరిపోలే ఉత్పత్తులు లేవు.',

  'inv.title': 'ఇన్వెంటరీ', 'inv.addProduct': 'ఉత్పత్తిని జోడించు', 'inv.searchProducts': 'ఉత్పత్తులను వెతకండి…',
  'inv.scanBarcode': 'బార్‌కోడ్ స్కాన్…', 'inv.stockValue': 'స్టాక్ విలువ (ధర వద్ద)', 'inv.labels': 'లేబుళ్లు',

  'khata.title': 'ఖాతా', 'khata.customers': 'కస్టమర్లు', 'khata.suppliers': 'సరఫరాదారులు', 'khata.addParty': 'పార్టీని జోడించు',

  'set.title': 'సెట్టింగ్‌లు', 'set.businessProfile': 'వ్యాపార ప్రొఫైల్ (ఇన్వాయిస్‌పై చూపబడుతుంది)',
  'set.preferences': 'ప్రాధాన్యతలు', 'set.account': 'ఖాతా & సభ్యత్వం', 'set.login': 'లాగిన్',
  'set.saveProfile': 'ప్రొఫైల్ సేవ్ చేయి', 'set.gstEnable': 'లావాదేవీలపై జీఎస్టీ ప్రారంభించు',
  'set.darkTheme': 'డార్క్ థీమ్', 'set.businessName': 'వ్యాపార పేరు',
};

const mr: Dict = {
  'lang.choose': 'तुमची भाषा निवडा',
  'lang.chooseSub': 'तुम्हाला वापरायची भाषा निवडा. ती नंतर सेटिंग्जमध्ये बदलता येईल.',
  'lang.continue': 'सुरू ठेवा', 'lang.label': 'भाषा',

  'common.save': 'जतन करा', 'common.cancel': 'रद्द करा', 'common.delete': 'हटवा',
  'common.edit': 'संपादित करा', 'common.search': 'शोधा', 'common.logout': 'लॉग आउट',
  'common.viewAll': 'सर्व पहा', 'common.total': 'एकूण', 'common.subtotal': 'उप-एकूण',
  'common.gst': 'जीएसटी', 'common.add': 'जोडा',

  'nav.dashboard': 'डॅशबोर्ड', 'nav.billing': 'बिलिंग', 'nav.inventory': 'इन्व्हेंटरी',
  'nav.khata': 'खाते', 'nav.reports': 'अहवाल', 'nav.settings': 'सेटिंग्ज', 'nav.admin': 'ॲडमिन',

  'login.sub': 'बिलिंग · इन्व्हेंटरी · खाते — तुमच्या सर्व डिव्हाइसवर सिंक',
  'login.google': 'Google ने सुरू ठेवा', 'login.or': 'किंवा', 'login.mobile': 'मोबाइल नंबर',
  'login.getOtp': 'OTP मिळवा', 'login.verify': 'पडताळा आणि लॉगिन करा', 'login.enterOtp': 'OTP प्रविष्ट करा',
  'login.change': '← नंबर बदला', 'login.codeSent': 'कोड पाठवला',
  'login.smsNote': 'तुमचा नंबर पडताळण्यासाठी SMS द्वारे एक-वेळ कोड पाठवला जातो.',

  'dash.overview': 'तुमच्या व्यवसायाचा आढावा', 'dash.todaySales': 'आजची विक्री',
  'dash.todayProfit': 'आजचा नफा', 'dash.billsToday': 'आज तयार केलेली बिले',
  'dash.lowStock': 'कमी स्टॉक असलेल्या वस्तू', 'dash.toCollect': 'येणे', 'dash.toPay': 'देणे',
  'dash.vsYesterday': 'कालच्या तुलनेत', 'dash.viewItems': 'वस्तू पहा', 'dash.viewDetails': 'तपशील पहा',
  'dash.salesOverview': 'विक्री आढावा', 'dash.businessSummary': 'व्यवसाय सारांश',
  'dash.totalSales': 'एकूण विक्री', 'dash.totalProfit': 'एकूण नफा',
  'dash.totalPurchases': 'एकूण खरेदी', 'dash.totalExpenses': 'एकूण खर्च',
  'dash.viewReport': 'संपूर्ण अहवाल पहा', 'dash.recentTxns': 'अलीकडील व्यवहार',
  'dash.viewAllItems': 'सर्व वस्तू पहा', 'dash.wellStocked': 'सर्व वस्तू पुरेशा स्टॉकमध्ये आहेत.',
  'dash.noTxns': 'अद्याप कोणतेही व्यवहार नाहीत.', 'dash.thisMonth': 'या महिन्यात',
  'dash.lastMonth': 'मागील महिना', 'dash.thisYear': 'या वर्षी', 'dash.newBill': 'नवीन बिल',
  'dash.needAttention': 'लक्ष आवश्यक', 'dash.available': 'उपलब्ध', 'dash.reorder': 'पुनःऑर्डर',
  'dash.status': 'स्थिती', 'dash.item': 'वस्तू', 'dash.category': 'श्रेणी',

  'bill.title': 'बिलिंग', 'bill.createInvoice': 'विक्री बीजक तयार करा',
  'bill.customer': 'ग्राहकाचे नाव', 'bill.cashSale': 'रोख विक्री (पर्यायी)',
  'bill.contact': 'संपर्क क्रमांक', 'bill.payMode': 'पेमेंट पद्धत',
  'bill.scan': 'बारकोड स्कॅन करा', 'bill.scanHint': 'येथे क्लिक करा, नंतर स्कॅन करा — वस्तू आपोआप जोडली जाते',
  'bill.searchProduct': 'उत्पादन शोधा (जलद जोडा)', 'bill.searchHint': 'शोधण्यासाठी टाइप करा, जोडण्यासाठी उत्पादनावर क्लिक करा…',
  'bill.category': 'श्रेणी', 'bill.allCategories': 'सर्व श्रेणी', 'bill.item': 'वस्तू',
  'bill.selectItem': '— वस्तू निवडा —', 'bill.brand': 'ब्रँड', 'bill.brandHint': 'वस्तूमधून आपोआप भरते',
  'bill.desc': 'उत्पादन वर्णन', 'bill.descHint': 'बीजकावर छापले जाते', 'bill.addToBill': 'बिलात जोडा',
  'bill.product': 'उत्पादन', 'bill.qty': 'प्रमाण', 'bill.rate': 'दर', 'bill.amountPaid': 'भरलेली रक्कम',
  'bill.saveBill': 'बिल जतन करा', 'bill.savePrint': 'जतन करा आणि प्रिंट करा', 'bill.clearBill': 'बिल साफ करा',
  'bill.startBill': 'बिल सुरू करण्यासाठी उत्पादने स्कॅन करा किंवा जोडा.', 'bill.noMatch': 'जुळणारी उत्पादने नाहीत.',

  'inv.title': 'इन्व्हेंटरी', 'inv.addProduct': 'उत्पादन जोडा', 'inv.searchProducts': 'उत्पादने शोधा…',
  'inv.scanBarcode': 'बारकोड स्कॅन करा…', 'inv.stockValue': 'स्टॉक मूल्य (किंमतीवर)', 'inv.labels': 'लेबल',

  'khata.title': 'खाते', 'khata.customers': 'ग्राहक', 'khata.suppliers': 'पुरवठादार', 'khata.addParty': 'पार्टी जोडा',

  'set.title': 'सेटिंग्ज', 'set.businessProfile': 'व्यवसाय प्रोफाइल (बीजकावर दिसते)',
  'set.preferences': 'प्राधान्ये', 'set.account': 'खाते आणि सदस्यत्व', 'set.login': 'लॉगिन',
  'set.saveProfile': 'प्रोफाइल जतन करा', 'set.gstEnable': 'व्यवहारांवर जीएसटी सक्षम करा',
  'set.darkTheme': 'डार्क थीम', 'set.businessName': 'व्यवसायाचे नाव',
};

const ta: Dict = {
  'lang.choose': 'உங்கள் மொழியைத் தேர்ந்தெடுக்கவும்',
  'lang.chooseSub': 'நீங்கள் பயன்படுத்த விரும்பும் மொழியைத் தேர்ந்தெடுக்கவும். பின்னர் அமைப்புகளில் மாற்றலாம்.',
  'lang.continue': 'தொடரவும்', 'lang.label': 'மொழி',

  'common.save': 'சேமி', 'common.cancel': 'ரத்து', 'common.delete': 'நீக்கு',
  'common.edit': 'திருத்து', 'common.search': 'தேடு', 'common.logout': 'வெளியேறு',
  'common.viewAll': 'அனைத்தையும் காண்க', 'common.total': 'மொத்தம்', 'common.subtotal': 'துணை மொத்தம்',
  'common.gst': 'ஜிஎஸ்டி', 'common.add': 'சேர்',

  'nav.dashboard': 'டாஷ்போர்டு', 'nav.billing': 'பில்லிங்', 'nav.inventory': 'சரக்கு',
  'nav.khata': 'கணக்கு', 'nav.reports': 'அறிக்கைகள்', 'nav.settings': 'அமைப்புகள்', 'nav.admin': 'நிர்வாகம்',

  'login.sub': 'பில்லிங் · சரக்கு · கணக்கு — உங்கள் அனைத்து சாதனங்களிலும் ஒத்திசைவு',
  'login.google': 'Google உடன் தொடரவும்', 'login.or': 'அல்லது', 'login.mobile': 'மொபைல் எண்',
  'login.getOtp': 'OTP பெறவும்', 'login.verify': 'சரிபார்த்து உள்நுழையவும்', 'login.enterOtp': 'OTP ஐ உள்ளிடவும்',
  'login.change': '← எண்ணை மாற்று', 'login.codeSent': 'குறியீடு அனுப்பப்பட்டது',
  'login.smsNote': 'உங்கள் எண்ணைச் சரிபார்க்க SMS மூலம் ஒரு முறை குறியீடு அனுப்பப்படும்.',

  'dash.overview': 'உங்கள் வணிகத்தின் மேலோட்டம்', 'dash.todaySales': 'இன்றைய விற்பனை',
  'dash.todayProfit': 'இன்றைய லாபம்', 'dash.billsToday': 'இன்று உருவாக்கிய பில்கள்',
  'dash.lowStock': 'குறைந்த சரக்கு பொருட்கள்', 'dash.toCollect': 'வசூலிக்க', 'dash.toPay': 'செலுத்த',
  'dash.vsYesterday': 'நேற்றுடன்', 'dash.viewItems': 'பொருட்களைக் காண்க', 'dash.viewDetails': 'விவரங்களைக் காண்க',
  'dash.salesOverview': 'விற்பனை கண்ணோட்டம்', 'dash.businessSummary': 'வணிக சுருக்கம்',
  'dash.totalSales': 'மொத்த விற்பனை', 'dash.totalProfit': 'மொத்த லாபம்',
  'dash.totalPurchases': 'மொத்த கொள்முதல்', 'dash.totalExpenses': 'மொத்த செலவுகள்',
  'dash.viewReport': 'முழு அறிக்கையைக் காண்க', 'dash.recentTxns': 'சமீபத்திய பரிவர்த்தனைகள்',
  'dash.viewAllItems': 'அனைத்து பொருட்களையும் காண்க', 'dash.wellStocked': 'அனைத்து பொருட்களும் போதுமான சரக்கில் உள்ளன.',
  'dash.noTxns': 'இதுவரை பரிவர்த்தனைகள் இல்லை.', 'dash.thisMonth': 'இந்த மாதம்',
  'dash.lastMonth': 'கடந்த மாதம்', 'dash.thisYear': 'இந்த ஆண்டு', 'dash.newBill': 'புதிய பில்',
  'dash.needAttention': 'கவனம் தேவை', 'dash.available': 'கிடைக்கும்', 'dash.reorder': 'மறு ஆர்டர்',
  'dash.status': 'நிலை', 'dash.item': 'பொருள்', 'dash.category': 'வகை',

  'bill.title': 'பில்லிங்', 'bill.createInvoice': 'விற்பனை விலைப்பட்டியல் உருவாக்கு',
  'bill.customer': 'வாடிக்கையாளர் பெயர்', 'bill.cashSale': 'ரொக்க விற்பனை (விருப்பம்)',
  'bill.contact': 'தொடர்பு எண்', 'bill.payMode': 'கட்டண முறை',
  'bill.scan': 'பார்கோடு ஸ்கேன்', 'bill.scanHint': 'இங்கே கிளிக் செய்து ஸ்கேன் செய்யவும் — பொருள் தானாகச் சேர்க்கப்படும்',
  'bill.searchProduct': 'பொருளைத் தேடு (விரைவு சேர்)', 'bill.searchHint': 'தேட தட்டச்சு செய்யவும், சேர்க்க பொருளைக் கிளிக் செய்யவும்…',
  'bill.category': 'வகை', 'bill.allCategories': 'அனைத்து வகைகள்', 'bill.item': 'பொருள்',
  'bill.selectItem': '— பொருளைத் தேர்ந்தெடு —', 'bill.brand': 'பிராண்ட்', 'bill.brandHint': 'பொருளிலிருந்து தானாக நிரப்பப்படும்',
  'bill.desc': 'பொருள் விளக்கம்', 'bill.descHint': 'விலைப்பட்டியலில் அச்சிடப்படும்', 'bill.addToBill': 'பில்லில் சேர்',
  'bill.product': 'பொருள்', 'bill.qty': 'அளவு', 'bill.rate': 'விலை', 'bill.amountPaid': 'செலுத்திய தொகை',
  'bill.saveBill': 'பில்லைச் சேமி', 'bill.savePrint': 'சேமித்து அச்சிடு', 'bill.clearBill': 'பில்லை அழி',
  'bill.startBill': 'பில்லைத் தொடங்க பொருட்களை ஸ்கேன் செய்யவும் அல்லது சேர்க்கவும்.', 'bill.noMatch': 'பொருந்தும் பொருட்கள் இல்லை.',

  'inv.title': 'சரக்கு', 'inv.addProduct': 'பொருள் சேர்', 'inv.searchProducts': 'பொருட்களைத் தேடு…',
  'inv.scanBarcode': 'பார்கோடு ஸ்கேன்…', 'inv.stockValue': 'சரக்கு மதிப்பு (விலையில்)', 'inv.labels': 'லேபிள்கள்',

  'khata.title': 'கணக்கு', 'khata.customers': 'வாடிக்கையாளர்கள்', 'khata.suppliers': 'சப்ளையர்கள்', 'khata.addParty': 'கட்சியைச் சேர்',

  'set.title': 'அமைப்புகள்', 'set.businessProfile': 'வணிக விவரம் (விலைப்பட்டியலில் காட்டப்படும்)',
  'set.preferences': 'விருப்பங்கள்', 'set.account': 'கணக்கு & சந்தா', 'set.login': 'உள்நுழைவு',
  'set.saveProfile': 'விவரத்தைச் சேமி', 'set.gstEnable': 'பரிவர்த்தனைகளில் ஜிஎஸ்டி இயக்கு',
  'set.darkTheme': 'இருண்ட தீம்', 'set.businessName': 'வணிகப் பெயர்',
};

export const TRANSLATIONS: Record<Lang, Dict> = { en, hi, te, mr, ta };
