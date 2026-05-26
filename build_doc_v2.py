from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

D = "/tmp/diagrams"
doc = Document()

for s in doc.sections:
    s.top_margin    = Cm(2.5)
    s.bottom_margin = Cm(2.5)
    s.left_margin   = Cm(3.0)
    s.right_margin  = Cm(2.0)

def run(p, text, bold=False, size=12, font='Times New Roman'):
    r = p.add_run(text)
    r.bold = bold; r.font.size = Pt(size); r.font.name = font
    return r

def cp(text, bold=False, size=12, sb=0, sa=6):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after  = Pt(sa)
    run(p, text, bold, size); return p

def bp(text, size=12, sb=4, sa=6):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after  = Pt(sa)
    run(p, text, False, size); return p

def lp(text, bold=False, size=12, sb=4, sa=4):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after  = Pt(sa)
    run(p, text, bold, size); return p

def bullet(text, size=12):
    p = doc.add_paragraph(style='List Bullet')
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run(p, text, False, size); return p

def num_bullet(text, size=12):
    p = doc.add_paragraph(style='List Number')
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run(p, text, False, size); return p

def sec_head(text, size=14):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after  = Pt(10)
    run(p, text, True, size); return p

def sub_head(text, size=12):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(4)
    run(p, text, True, size); return p

def img(path, w_cm=13, caption=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(6)
    p.add_run().add_picture(path, width=Cm(w_cm))
    if caption:
        c = doc.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraph_format.space_before = Pt(2)
        c.paragraph_format.space_after  = Pt(12)
        run(c, caption, True, 11)

def pb(): doc.add_page_break()

# ══════════════════════════════════════════════════════════════
# PAGE 1 – TITLE PAGE
# ══════════════════════════════════════════════════════════════
cp("Blockchain-based Authorization Mechanism for", True, 16, 24, 2)
cp("Educational Social Internet of Things",        True, 16,  0, 20)
cp("A Main project report submitted in partial fulfillment of the degree", False, 12, 8, 4)
cp("Master of Technology", True, 14, 4, 2)
cp("In",                   False,12, 2, 2)
cp("COMPUTER SCIENCE AND ENGINEERING", True, 13, 4, 12)
cp("By", False, 12, 6, 4)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(4)
p.paragraph_format.space_after  = Pt(4)
run(p, "REVURI NIKITHA", True, 13)
run(p, "        24CD1D5825", True, 13)
cp("", False, 6)
cp("Under the guidance of",   False,12, 10, 4)
cp("DR. G. JOSE MARY",        True, 13,  2, 2)
cp("(Assoc. Professor)",      False,12,  0, 22)
cp("DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING", True, 12, 10, 4)
cp("JAYAMUKHI INSTITUTE OF TECHNOLOGICAL SCIENCES",  True, 13,  2, 2)
cp("(UGC-AUTONOMOUS) NARSAMPET, WARANGAL-506332",    False,12,  0, 2)
cp("(Accredited with NAAC A & Affiliated to JNTUH)", False,12,  0, 4)

# ══════════════════════════════════════════════════════════════
# PAGE 2 – CERTIFICATE
# ══════════════════════════════════════════════════════════════
pb()
cp("JAYAMUKHI INSTITUTE OF TECHNOLOGICAL SCIENCES",  True, 13, 20, 4)
cp("(UGC-AUTONOMOUS) NARSAMPET, WARANGAL-506332",    False,12,  0, 4)
cp("(Accredited with NAAC A & Affiliated to JNTUH)", False,12,  0, 30)
cp("CERTIFICATE", True, 16, 20, 18)
bp('This is to certify that the Main Project Report entitled '
   '"Blockchain-based Authorization Mechanism for Educational Social '
   'Internet of Things" is a bonafide work of the student REVURI NIKITHA '
   '(24CD1D5825) submitted in partial fulfillment of the requirements for '
   'the award of the degree of Master of Technology in CSE during the '
   'academic year 2024-26.')
for _ in range(4): cp("", False, 12)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
p.paragraph_format.space_before = Pt(36)
run(p, "Guide", True, 12)
run(p, "\t\t\t\t\tHead of the Department", True, 12)

# ══════════════════════════════════════════════════════════════
# PAGE 3 – ACKNOWLEDGEMENT
# ══════════════════════════════════════════════════════════════
pb()
sec_head("ACKNOWLEDGEMENT", 16)
cp("", False, 10)
bp("I express my immense gratitude and sincere thanks to Dr. V. JANAKI, "
   "Principal of Jayamukhi Institute of Technological Sciences, Narsampet, "
   "Warangal for her constant motivation and support.")
bp("I have immense pleasure in expressing my sincere thanks to "
   "Dr. G. JOSEMARY, Head of Computer Science and Engineering Department "
   "and Project Guide, who inspired me in my work and for valuable guidance.")
bp("I am also thankful to my management for providing all the facilities "
   "for completing the project.")
cp("", False, 12)
cp("THANK YOU", True, 13, 10, 18)
for _ in range(4): cp("", False, 12)
cp("REVURI NIKITHA", True,  12, 18, 2)
cp("24CD1D5825",     False, 12,  0, 4)

# ══════════════════════════════════════════════════════════════
# PAGE 4 – ABSTRACT
# ══════════════════════════════════════════════════════════════
pb()
sec_head("ABSTRACT", 16)
bp("The Social Internet of Things (SIoT) paradigm has been integrated in "
   "the education domain to enable educational IoT devices to establish "
   "social relationships and exchange academic services. Nonetheless, the "
   "social relationships are not adapted to the educational context where "
   "devices must be socially linked based on their academic roles and "
   "activities. Furthermore, the exchange of services raises the requirement "
   "to implement an access control mechanism. In SIoT, social constraints "
   "such as the social relationship type and contact frequency are critical "
   "requirements to make an access decision. However, these constraints "
   "cannot be specified using the eXtensible Access Control Markup Language "
   "(XACML) standard as device attributes nor as contextual conditions. In "
   "this paper, we propose an Educational Social Internet of Things "
   "(EducationalSIoT) platform implemented as an application-specific "
   "blockchain where we define new social relationships for educational "
   "devices. To control the access to the academic services, we suggest "
   "extending the XACML policy model by considering the social requirements, "
   "and accordingly, we adjust the policy evaluation process and suggest "
   "priority-based combining algorithms. Additionally, our platform ensures "
   "the delegation of access permission by defining delegation policies and "
   "controlling the delegation operation with consideration of the social "
   "features. The simulation results show that by integrating social "
   "features, an access request is evaluated in 0.22ms and a delegation "
   "request is evaluated in 0.32ms. Finally, we guarantee that our platform "
   "is protected against the man-in-the-middle and replay attacks.")

# ══════════════════════════════════════════════════════════════
# PAGE 5 – INDEX
# ══════════════════════════════════════════════════════════════
pb()
sec_head("INDEX", 16)
tbl = doc.add_table(rows=1, cols=3)
tbl.style = 'Table Grid'
for i, h in enumerate(['Sl.no', 'Topic Name', 'Page No']):
    tbl.rows[0].cells[i].text = h
    for para in tbl.rows[0].cells[i].paragraphs:
        for r in para.runs: r.bold = True; r.font.size = Pt(12)
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
INDEX = [
    ("1.",  "INTRODUCTION",             "1-3"),
    ("2.",  "FEASIBILITY STUDY",        "4-7"),
    ("3.",  "SYSTEM STUDY",             "8-9"),
    ("4.",  "SOFTWARE ENVIRONMENT",     "11-15"),
    ("5.",  "J2EE SOFTWARE ENVIRONMENT","16-20"),
    ("6.",  "ARCHITECTURE CLASS DIAGRAM","21-25"),
    ("7.",  "MODULES",                  "26-30"),
    ("8.",  "Data Flow Diagram",        "31-35"),
    ("9.",  "Use Case Diagram",         "36-40"),
    ("10.", "Sequence Diagram",         "41-50"),
    ("11.", "Flow Chart Diagram",       "51-55"),
    ("12.", "TESTING",                  "56-58"),
    ("13.", "CONCLUSION",               "59"),
    ("14.", "REFERENCES",               "60"),
]
for num, topic, pg in INDEX:
    row = tbl.add_row().cells
    row[0].text = num; row[1].text = topic; row[2].text = pg
    for i, cell in enumerate(row):
        for para in cell.paragraphs:
            for r2 in para.runs: r2.font.size = Pt(12)
            if i != 1: para.alignment = WD_ALIGN_PARAGRAPH.CENTER

# ══════════════════════════════════════════════════════════════
# CH 1 – INTRODUCTION
# ══════════════════════════════════════════════════════════════
pb()
sec_head("INTRODUCTION", 14)
bp("EDUCATION without technology becomes worthless. With the new advances "
   "in Information and Communication Technology (ICT) and its impact in "
   "transforming domains, several educational institutions (e.g. schools, "
   "universities) invest to incorporate the Internet of Things (IoT) "
   "technology. The IoT transforms the traditional education to smart "
   "education in order to provide smart services such as smart pedagogy, "
   "smart classrooms and smart administration. To extend its capabilities "
   "with cooperative services such as service discovery, the IoT is combined "
   "with the social network concept leading to an emerging paradigm known as "
   "the Social Internet of Things (SIoT). SIoT applies the social networking "
   "principles to the IoT. It allows smart devices to become social by "
   "autonomously forming social connections with the respect of socialization "
   "rules set by their owners.")
bp("In order to face the scalability of IoT devices and provide a "
   "decentralized architecture, the blockchain technology, known as "
   "Distributed Applications (DApps), has been integrated with the SIoT "
   "(e.g. BlockSIoT). Nevertheless, the applicability of blockchains "
   "combined with the SIoT to the educational context faces three main "
   "challenges: the limitations of the DApps blockchain technology, the "
   "inadaptability of social relationships to the educational context, and "
   "the requirement to secure access to the academic services.")
bp("On the one hand, DApps such as Ethereum are widely employed for "
   "distributed architecture, no central authority, transaction logging and "
   "transparency purposes. The DApps business logic can be customized only "
   "by deploying smart contracts. However, smart contracts represent barriers "
   "to developing more complex applications due to the immature ecosystem of "
   "the solidity language. For instance, they cannot incorporate the machine "
   "learning or deep learning models to build smart blockchains which train "
   "data, generate models and make smart decisions. In addition, they must "
   "be re-deployed with any new changes.")
bp("On the other hand, IoT devices deployed inside an academic institution "
   "(e.g. smart whiteboards) and handheld and wearable objects (e.g. smart "
   "glasses) leveraged in the learning process form a new sub-category of "
   "IoT known as the Internet of Educational Things (IoET). The social "
   "relationships such as the co-location and co-work relationships are "
   "used for the general SIoT purposes. For instance, the instructors allow "
   "their tablets to establish co-work social relationships with the smart "
   "whiteboard during their class. However, the social relationships formed "
   "between IoET devices need to be customized for the educational context. "
   "For example, to explain a medical procedure, the instructor can share a "
   "video from his laptop to smart glasses worn by medical students and "
   "trainees.")
bp("Moreover, the exchange of data and services between the social devices "
   "raises the requirement to control the access to these resources (i.e. "
   "data and services). To provide an effective protection and prevent "
   "unauthorized access, the eXtensible Access Control Markup Language "
   "(XACML) is leveraged to implement an authorization component such as "
   "the case of the SocIoTal. XACML is a fine-grained and attribute-based "
   "authorization policy specification language standardised by the OASIS "
   "standards consortium. It proposes a policy model where a policy set is "
   "composed of policy sets and/or policies, and a policy contains a set "
   "of rules.")
bp("In the context of a social network of IoET devices, a social device "
   "needs to allow only devices with specific social relationship type, "
   "social similarity, trustworthiness degree, social activeness, social "
   "contact frequency and social contact duration to access their data and "
   "services. Therefore, there is an imperative requirement to express these "
   "social constraints as access requirements in XACML. The similarity, the "
   "trustworthiness and the social activeness are social device features. "
   "Thus, they can be expressed in XACML as attributes of the access "
   "requester device (i.e. subject) or attributes of the requested device "
   "(i.e. resource). However, the social relationship type, the social "
   "contact frequency and the social contact duration cannot be expressed "
   "as device attributes nor as contextual conditions. They are social "
   "features that describe the social relationship between two social devices.")

sub_head("EducationalSIoT Platform Overview")
bp("The EducationalSIoT platform is designed to address the three main "
   "challenges of applying blockchain-based SIoT to the educational context. "
   "The platform is implemented as an application-specific blockchain using "
   "the Cosmos SDK framework. The application-specific blockchain approach "
   "offers several advantages over general-purpose DApps:")
bullet("Full customization of the blockchain logic without the constraints "
       "of smart contract languages.")
bullet("Ability to incorporate machine learning models directly as blockchain "
       "modules for intelligent EIOT device classification.")
bullet("Faster transaction processing with consensus finality in seconds "
       "rather than minutes.")
bullet("Lower transaction costs compared to Ethereum gas fees.")
bullet("Direct integration with the XACML policy evaluation engine without "
       "the need for middleware.")
bp("The platform defines two new types of social relationships specifically "
   "designed for the educational context:")
bullet("Class Object Relationship (ClsOR): A social relationship established "
       "between IoET devices that are used together in the same class session. "
       "For example, the instructor's laptop and a student's tablet used in "
       "the same course lecture form a ClsOR. This relationship captures the "
       "temporal and contextual nature of class activities.")
bullet("Institution Object Relationship (InsOR): A social relationship "
       "established between IoET devices that belong to the same educational "
       "institution. For example, two smart whiteboards from different "
       "classrooms in the same university form an InsOR. This relationship "
       "captures the organizational affiliation of devices.")
bp("These new social relationship types enable the platform to make "
   "fine-grained access control decisions based on the educational context "
   "of the devices. For example, a student's tablet can be granted access "
   "to share content from the instructor's laptop only if there is an active "
   "ClsOR between them with sufficient contact frequency and duration.")

sec_head("EXISTING SYSTEM", 13)
bp("IoT devices deployed inside an academic institution (e.g. smart "
   "whiteboards) and handheld and wearable objects (e.g. smart glasses) "
   "leveraged in the learning process form a new sub-category of IoT known "
   "as the Internet of Educational Things (IoET). The social relationships "
   "such as the co-location and co-work relationships are used for the "
   "general SIoT purposes. For instance, the instructors allow their tablets "
   "to establish co-work social relationships with the smart whiteboard "
   "during their class. However, the social relationships formed between "
   "IoET devices need to be customized for the educational context.")
bp("To provide an effective protection and prevent unauthorized access, the "
   "eXtensible Access Control Markup Language (XACML) is leveraged to "
   "implement an authorization component. XACML is a fine-grained and "
   "attribute-based authorization policy specification language standardised "
   "by the OASIS standards consortium. It proposes a policy model where a "
   "policy set is composed of policy sets and/or policies, and a policy "
   "contains a set of rules. In the existing systems, social relationship "
   "constraints such as the social relationship type, the social contact "
   "frequency and the social contact duration cannot be expressed as device "
   "attributes nor as contextual conditions. They are social features that "
   "describe the social relationship between two social devices. In addition, "
   "the XACML standard does not support the specification of the social "
   "relationship constraints as access control requirements.")
bp("Blockchain-based access control mechanisms have been implemented to "
   "secure the access to shared resources. The public key infrastructure is "
   "widely used for authentication where a user public key can be leveraged "
   "to authorize the access if this public key is specified in the authorized "
   "policy list. To secure access to healthcare data in emergency situations, "
   "the smart contracts are leveraged to implement the Role-Based Access "
   "Control (RBAC) model. Additionally, smart contracts play an important "
   "role in automatically executing the evaluation of the access permissions. "
   "However, existing delegation policy models cannot consider the social "
   "requirements to control the delegation operation.")
sub_head("Disadvantages")
bullet("There is no mechanism to incorporate social relationship constraints "
       "such as social relationship type, contact frequency and contact "
       "duration into XACML access control policies in existing systems.")
bullet("The existing DApps blockchain technology using Ethereum cannot "
       "incorporate machine learning or deep learning models and must be "
       "re-deployed with any new changes.")

sub_head("Proposed System")
bullet("We review the social features and we present their existing "
       "classifications. Then, we propose new classifications based on the "
       "nature, the dynamicity and the type of the feature.")
bullet("We propose an Educational Social Internet of Things (EducationalSIoT) "
       "platform implemented as an application-specific blockchain. To the "
       "best of our knowledge, no existing work comes up with a proposition "
       "for an educational platform based on the social network of IoET "
       "devices and the application-specific blockchain technology.")
bullet("In order to adapt social relationships to roles and activities of "
       "IoET devices in an academic institution, we define two new types of "
       "social relationships: Class Object Relationship (ClsOR) and "
       "Institution Object Relationship (InsOR).")
bullet("We extend the XACML policy model and propose a delegation policy "
       "model to specify the social constraints required for making an access "
       "decision or a delegation decision, respectively.")
bullet("To allow access and perform delegation operations in emergency "
       "situations, we propose to assign a priority to rules and policies "
       "and we suggest new priority-based combining algorithms.")

sub_head("Advantages")
bp("The proposed EducationalSIoT platform integrates social features into "
   "the XACML authorization mechanism. The similarity, the trustworthiness "
   "and the social activeness are social device features that can be "
   "expressed in XACML as attributes. The social relationship type, the "
   "social contact frequency and the social contact duration are incorporated "
   "as social conditions in the policy model. This provides fine-grained, "
   "social-aware access control for Educational IoT environments with an "
   "access request evaluation time of 0.22ms and delegation request "
   "evaluation time of 0.32ms, ensuring scalability and performance.")

sec_head("SYSTEM REQUIREMENTS", 13)
sub_head("H/W System Configuration:-")
for name, val in [("Processor","Pentium-IV"),("RAM","4 GB (min)"),
                  ("Hard Disk","20 GB"),("Key Board","Standard Windows Keyboard"),
                  ("Mouse","Two or Three Button Mouse"),("Monitor","SVGA")]:
    bullet(f"{name}   -   {val}")
sub_head("Software Requirements:")
for name, val in [("Operating System","Windows XP"),
                  ("Coding Language","Java/J2EE(JSP,Servlet)"),
                  ("Front End","J2EE"),("Back End","MySQL")]:
    bullet(f"{name}   -   {val}")

# ══════════════════════════════════════════════════════════════
# CH 2 – FEASIBILITY STUDY
# ══════════════════════════════════════════════════════════════
pb()
sec_head("FEASIBILITY STUDY", 14)

sub_head("PRELIMINARY INVESTIGATION")
bp("The first and foremost strategy for development of a project starts from "
   "the thought of designing a blockchain-based educational IoT platform in "
   "which it is easy and convenient to manage IoET devices, define social "
   "relationships, control access to academic services, and delegate access "
   "permissions. When it is approved by the organization and our project "
   "guide the first activity, i.e. preliminary investigation begins. "
   "The activity has three parts:")
for item in ["Request Clarification","Feasibility Study","Request Approval"]:
    bullet(item)

sub_head("REQUEST CLARIFICATION")
bp("After the approval of the request to the organization and project guide, "
   "with an investigation being considered, the project request must be "
   "examined to determine precisely what the system requires. Here our "
   "project is basically meant for educational institutions whose IoET "
   "devices can be interconnected through a blockchain-based platform. "
   "In today's digital age, smart education requires secure and efficient "
   "management of IoET devices along with a robust access control mechanism "
   "that considers the social relationship features of the devices.")

sub_head("FEASIBILITY ANALYSIS")
bp("An important outcome of preliminary investigation is the determination "
   "that the system request is feasible. This is possible only if it is "
   "feasible within limited resource and time. The different feasibilities "
   "that have to be analyzed are:")
for item in ["Operational Feasibility","Economic Feasibility","Technical Feasibility"]:
    bullet(item)
bp("Operational Feasibility deals with the study of prospects of the system "
   "to be developed. This system operationally eliminates all the tensions "
   "of the Admin and helps him in effectively managing IoET devices, social "
   "relationships and access control policies. This kind of automation will "
   "surely reduce the time and energy, which previously consumed in manual "
   "work. Based on the study, the system is proved to be operationally feasible.")

sub_head("Economic Feasibility")
bp("Economic Feasibility or Cost-benefit is an assessment of the economic "
   "justification for a computer based project. As hardware was installed "
   "from the beginning and for lots of purposes thus the cost on project of "
   "hardware is low. The EducationalSIoT platform leverages open-source "
   "blockchain technology (Cosmos SDK), Java/J2EE for development, and "
   "MySQL for database, all of which are freely available. Since the system "
   "is a network based, any number of IoET devices connected to the platform "
   "within that organization can use this tool at anytime. So the project "
   "is economically feasible.")

sub_head("Technical Feasibility")
bp("According to Roger S. Pressman, Technical Feasibility is the assessment "
   "of the technical resources of the organization. The organization needs "
   "IBM compatible machines with a graphical web browser connected to the "
   "Internet and Intranet. The system is developed for a platform-independent "
   "environment using Java Server Pages, JavaScript, HTML, SQL server and "
   "WebLogic Server. The technical feasibility has been carried out. The "
   "system is technically feasible for development and can be developed with "
   "the existing facility.")

sub_head("REQUEST APPROVAL")
bp("Not all request projects are desirable or feasible. Some organizations "
   "receive so many project requests from client users that only few of them "
   "are pursued. However, those projects that are both feasible and desirable "
   "should be put into schedule. After a project request is approved, its "
   "cost, priority, completion time and personnel requirement is estimated "
   "and used to determine where to add it to any project list. Truly "
   "speaking, the approval of those above factors, development works can be "
   "launched.")

sec_head("SYSTEM DESIGN AND DEVELOPMENT", 13)

sub_head("INPUT DESIGN")
bp("Input Design plays a vital role in the life cycle of software development; "
   "it requires very careful attention of developers. The input design is to "
   "feed data to the application as accurately as possible. So inputs are "
   "supposed to be designed effectively so that the errors occurring while "
   "feeding are minimized. According to Software Engineering Concepts, the "
   "input forms or screens are designed to provide validation control over "
   "the input limit, range and other related validations.")
bp("This system has input screens in almost all the modules. Error messages "
   "are developed to alert the user whenever he commits some mistakes and "
   "guides him in the right way so that invalid entries are not made. Let us "
   "see deeply about this under module design.")
bp("Input design is the process of converting the user created input into a "
   "computer-based format. The goal of the input design is to make the data "
   "entry logical and free from errors. The error in the input are controlled "
   "by the input design. The application has been developed in a user-friendly "
   "manner. The forms have been designed in such a way during the processing "
   "the cursor is placed in the position where must be entered. The user is "
   "also provided with an option to select an appropriate input from various "
   "alternatives related to the field in certain cases.")
bp("Validations are required for each data entered. Whenever a user enters "
   "an erroneous data, error message is displayed and the user can move on "
   "to the subsequent pages after completing all the entries in the current page.")

sub_head("OUTPUT DESIGN")
bp("The Output from the computer is required to mainly create an efficient "
   "method of communication within the educational institution primarily "
   "among the administrator, teachers and students. The output of the "
   "EducationalSIoT system allows the administrator to manage IoET devices, "
   "define access control policies using XACML, monitor social relationships "
   "between IoET devices, view EIOT device results, e-learning board type "
   "results, institution type results and education level results. After "
   "completion of an access policy, a new delegation may be assigned to the "
   "user. User authentication procedures are maintained at the initial "
   "stages itself. A new user may be created by the administrator himself "
   "or a user can himself register as a new user but the task of assigning "
   "access policies and validating a new user rests with the administrator only.")
bp("The application starts running when it is executed for the first time. "
   "The server has to be started and then the internet explorer is used as "
   "the browser. The project will run on the local area network so the server "
   "machine will serve as the administrator while the other connected systems "
   "can act as the clients. The developed system is highly user friendly and "
   "can be easily understood by anyone using it even for the first time.")

# ══════════════════════════════════════════════════════════════
# CH 3 – SYSTEM STUDY
# ══════════════════════════════════════════════════════════════
pb()
sec_head("SYSTEM STUDY", 14)

sub_head("FEASIBILITY STUDY")
bp("The feasibility of the project is analyzed in this phase and business "
   "proposal is put forth with a very general plan for the project and some "
   "cost estimates. During system analysis the feasibility study of the "
   "proposed system is to be carried out. This is to ensure that the proposed "
   "system is not a burden to the company. For feasibility analysis, some "
   "understanding of the major requirements for the system is essential.")
bp("Three key considerations involved in the feasibility analysis are:")
for item in ["ECONOMICAL FEASIBILITY","TECHNICAL FEASIBILITY","SOCIAL FEASIBILITY"]:
    bullet(item)

sub_head("ECONOMICAL FEASIBILITY")
bp("This study is carried out to check the economic impact that the system "
   "will have on the organization. The amount of fund that the company can "
   "pour into the research and development of the system is limited. The "
   "expenditures must be justified. Thus the developed system is well within "
   "the budget and this was achieved because most of the technologies used "
   "are freely available. Only the customized products had to be purchased.")

sub_head("TECHNICAL FEASIBILITY")
bp("This study is carried out to check the technical feasibility, that is, "
   "the technical requirements of the system. Any system developed must not "
   "have a high demand on the available technical resources. This will lead "
   "to high demands being placed on the client. The developed system must "
   "have a modest requirement, as only minimal or null changes are required "
   "for implementing this system. The EducationalSIoT platform is built using "
   "Cosmos SDK for blockchain, Java/J2EE for web application, and MySQL for "
   "data storage, all of which are technically feasible.")

sub_head("SOCIAL FEASIBILITY")
bp("The aspect of study is to check the level of acceptance of the system "
   "by the user. This includes the process of training the user to use the "
   "system efficiently. The user must not feel threatened by the system, "
   "instead must accept it as a necessity. The level of acceptance by the "
   "users solely depends on the methods that are employed to educate the "
   "user about the system and to make him familiar with it. His level of "
   "confidence must be raised so that he is also able to make some "
   "constructive criticism, which is welcomed, as he is the final user "
   "of the system.")

# blank separator page (page 10 in Likith's structure)
pb()
cp("", False, 12, 200, 6)

# ══════════════════════════════════════════════════════════════
# CH 4 – SOFTWARE ENVIRONMENT (FULL CONTENT)
# ══════════════════════════════════════════════════════════════
pb()
sec_head("Software Environment", 14)

sub_head("Java Technology")
bp("Java technology is both a programming language and a platform.")

sub_head("The Java Programming Language")
bp("The Java programming language is a high-level language that can be "
   "characterized by all of the following buzzwords:")
for feat in ["Simple","Architecture neutral","Object oriented","Portable",
             "Distributed","High performance","Interpreted","Multithreaded",
             "Robust","Dynamic","Secure"]:
    bullet(feat)

bp("With most programming languages, you either compile or interpret a "
   "program so that you can run it on your computer. The Java programming "
   "language is unusual in that a program is both compiled and interpreted. "
   "With the compiler, first you translate a program into an intermediate "
   "language called Java byte codes - the platform-independent codes "
   "interpreted by the interpreter on the Java platform. The interpreter "
   "parses and runs each Java byte code instruction on the computer. "
   "Compilation happens just once; interpretation occurs each time the "
   "program is executed. The following figure illustrates how this works.")

bp("You can think of Java byte codes as the machine code instructions for "
   "the Java Virtual Machine (Java VM). Every Java interpreter, whether it's "
   "a development tool or a Web browser that can run applets, is an "
   "implementation of the Java VM. Java byte codes help make 'write once, "
   "run anywhere' possible. You can compile your program into byte codes on "
   "any platform that has a Java compiler. The byte codes can then be run on "
   "any implementation of the Java VM. That means that as long as a computer "
   "has a Java VM, the same program written in the Java programming language "
   "can run on Windows 2000, a Solaris workstation, or on an iMac.")

sub_head("The Java Platform")
bp("A platform is the hardware or software environment in which a program "
   "runs. We've already mentioned some of the most popular platforms like "
   "Windows 2000, Linux, Solaris, and MacOS. Most platforms can be described "
   "as a combination of the operating system and hardware. The Java platform "
   "differs from most other platforms in that it's a software-only platform "
   "that runs on top of other hardware-based platforms.")
bp("The Java platform has two components:")
bullet("The Java Virtual Machine (Java VM)")
bullet("The Java Application Programming Interface (Java API)")
bp("You've already been introduced to the Java VM. It's the base for the "
   "Java platform and is ported onto various hardware-based platforms. "
   "The Java API is a large collection of ready-made software components "
   "that provide many useful capabilities, such as graphical user interface "
   "(GUI) widgets. The Java API is grouped into libraries of related classes "
   "and interfaces; these libraries are known as packages.")
bp("Native code is code that after you compile it, the compiled code runs on "
   "a specific hardware platform. As a platform-independent environment, the "
   "Java platform can be a bit slower than native code. However, smart "
   "compilers, well-tuned interpreters, and just-in-time byte code compilers "
   "can bring performance close to that of native code without threatening portability.")
bp("The most common types of programs written in the Java programming language "
   "are applets and applications. An applet is a program that adheres to "
   "certain conventions that allow it to run within a Java-enabled browser. "
   "The general-purpose, high-level Java programming language is also a "
   "powerful software platform. Using the generous API, you can write many "
   "types of programs.")

sub_head("How Will Java Technology Change My Life?")
bp("We can't promise you fame, fortune, or even a job if you learn the Java "
   "programming language. Still, it is likely to make your programs better "
   "and requires less effort than other languages. We believe that Java "
   "technology will help you do the following:")
bullet("Get started quickly: Although the Java programming language is a powerful "
       "object-oriented language, it's easy to learn, especially for programmers "
       "already familiar with C or C++.")
bullet("Write less code: Comparisons of program metrics suggest that a program "
       "written in the Java programming language can be four times smaller than "
       "the same program in C++.")
bullet("Write better code: The Java programming language encourages good coding "
       "practices, and its garbage collection helps you avoid memory leaks.")
bullet("Develop programs more quickly: Your development time may be as much as "
       "twice as fast versus writing the same program in C++.")
bullet("Avoid platform dependencies with 100% Pure Java: You can keep your "
       "program portable by avoiding the use of libraries written in other languages.")
bullet("Write once, run anywhere: Because 100% Pure Java programs are compiled "
       "into machine-independent byte codes, they run consistently on any Java platform.")
bullet("Distribute software more easily: You can upgrade applets easily from a "
       "central server. Applets take advantage of the feature of allowing new "
       "classes to be loaded 'on the fly,' without recompiling the entire program.")

sub_head("ODBC")
bp("Microsoft Open Database Connectivity (ODBC) is a standard programming "
   "interface for application developers and database systems providers. "
   "Before ODBC became a de facto standard for Windows programs to interface "
   "with database systems, programmers had to use proprietary languages for "
   "each database they wanted to connect to. Now, ODBC has made the choice "
   "of the database system almost irrelevant from a coding perspective, which "
   "is as it should be. Application developers have much more important things "
   "to worry about than the syntax that is needed to port their program from "
   "one database to another when business needs suddenly change.")
bp("Through the ODBC Administrator in Control Panel, you can specify the "
   "particular database that is associated with a data source that an ODBC "
   "application program is written to use. Think of an ODBC data source as a "
   "door with a name on it. Each door will lead you to a particular database. "
   "For example, the data source named Sales Figures might be a SQL Server "
   "database, whereas the Accounts Payable data source could refer to an "
   "Access database. The physical database referred to by a data source can "
   "reside anywhere on the LAN.")
bp("From a programming perspective, the beauty of ODBC is that the application "
   "can be written to use the same set of function calls to interface with any "
   "data source, regardless of the database vendor. The source code of the "
   "application doesn't change whether it talks to Oracle or SQL Server. "
   "There are ODBC drivers available for several dozen popular database systems. "
   "Even Excel spreadsheets and plain text files can be turned into data sources. "
   "The operating system uses the Registry information written by ODBC "
   "Administrator to determine which low-level ODBC drivers are needed to talk "
   "to the data source. The loading of the ODBC drivers is transparent to the "
   "ODBC application program.")
bp("The advantages of this scheme are so numerous that you are probably "
   "thinking there must be some catch. The only disadvantage of ODBC is that "
   "it isn't as efficient as talking directly to the native database interface. "
   "ODBC has had many detractors make the charge that it is too slow. Microsoft "
   "has always claimed that the critical factor in performance is the quality "
   "of the driver software that is used. The availability of good ODBC drivers "
   "has improved a great deal recently. And anyway, the criticism about "
   "performance is somewhat analogous to those who said that compilers would "
   "never match the speed of pure assembly language.")

sub_head("JDBC")
bp("In an effort to set an independent database standard API for Java; Sun "
   "Microsystems developed Java Database Connectivity, or JDBC. JDBC offers "
   "a generic SQL database access mechanism that provides a consistent "
   "interface to a variety of RDBMSs. This consistent interface is achieved "
   "through the use of 'plug-in' database connectivity modules, or drivers. "
   "If a database vendor wishes to have JDBC support, he or she must provide "
   "the driver for each platform that the database and Java run on.")
bp("To gain a wider acceptance of JDBC, Sun based JDBC's framework on ODBC. "
   "As you discovered earlier in this chapter, ODBC has widespread support on "
   "a variety of platforms. Basing JDBC on ODBC will allow vendors to bring "
   "JDBC drivers to market much faster than developing a completely new "
   "connectivity solution. JDBC was announced in March of 1996. It was "
   "released for a 90 day public review that ended June 8, 1996. Because of "
   "user input, the final JDBC v1.0 specification was released soon after.")

sub_head("JDBC Goals")
bp("Few software packages are designed without goals in mind. JDBC is one "
   "that, because of its many goals, drove the development of the API. These "
   "goals, in conjunction with early reviewer feedback, have finalized the "
   "JDBC class library into a solid framework for building database "
   "applications in Java. The eight design goals for JDBC are as follows:")
num_bullet("SQL Level API: The designers felt that their main goal was to define "
           "a SQL interface for Java. Although not the lowest database interface "
           "level possible, it is at a low enough level for higher-level tools "
           "and APIs to be created.")
num_bullet("SQL Conformance: SQL syntax varies as you move from database vendor "
           "to database vendor. In an effort to support a wide variety of "
           "vendors, JDBC will allow any query statement to be passed through "
           "it to the underlying database driver.")
num_bullet("JDBC must be implementable on top of common database interfaces: "
           "The JDBC SQL API must 'sit' on top of other common SQL level APIs. "
           "This goal allows JDBC to use existing ODBC level drivers by the use "
           "of a software interface.")
num_bullet("Provide a Java interface that is consistent with the rest of the "
           "Java system: Because of Java's acceptance in the user community thus "
           "far, the designers feel that they should not stray from the current "
           "design of the core Java system.")
num_bullet("Keep it simple: This goal probably appears in all software design "
           "goal listings. Sun felt that the design of JDBC should be very "
           "simple, allowing for only one method of completing a task per mechanism.")
num_bullet("Use strong, static typing wherever possible: Strong typing allows "
           "for more error checking to be done at compile time; also, less "
           "errors appear at runtime.")
num_bullet("Keep the common cases simple: Because more often than not, the usual "
           "SQL calls used by the programmer are simple SELECT's, INSERT's, "
           "DELETE's and UPDATE's, these queries should be simple to perform "
           "with JDBC. However, more complex SQL statements should also be possible.")
num_bullet("Transaction support: JDBC provides full transaction management "
           "capabilities, allowing the programmer to commit or rollback a set "
           "of database operations as a unit.")

sub_head("JFree Chart")
bp("JFreeChart is a free 100% Java chart library that makes it easy for "
   "developers to display professional quality charts in their applications. "
   "JFreeChart's extensive feature set includes:")
bullet("A consistent and well-documented API, supporting a wide range of chart types.")
bullet("A flexible design that is easy to extend, and targets both server-side "
       "and client-side applications.")
bullet("Support for many output types, including Swing components, image files "
       "(including PNG and JPEG), and vector graphics file formats (including "
       "PDF, EPS and SVG).")
bp("JFreeChart is 'open source' or, more specifically, free software. It is "
   "distributed under the terms of the GNU Lesser General Public Licence "
   "(LGPL), which permits use in proprietary applications.")

sub_head("Networking")
bp("TCP/IP stack:")
bp("The TCP/IP stack is shorter than the OSI one. TCP is a "
   "connection-oriented protocol; UDP (User Datagram Protocol) is a "
   "connectionless protocol.")
sub_head("IP datagrams")
bp("The IP layer provides a connectionless and unreliable delivery system. "
   "It considers each datagram independently of the others. Any association "
   "between datagrams must be supplied by the higher layers. The IP layer "
   "supplies a checksum that includes its own header. The header includes "
   "the source and destination addresses. The IP layer handles routing "
   "through an Internet. It is also responsible for breaking up large "
   "datagrams into smaller ones for transmission and reassembling them "
   "at the other end.")
sub_head("UDP")
bp("UDP is also connectionless and unreliable. What it adds to IP is a "
   "checksum for the contents of the datagram and port numbers. These are "
   "used to give a client/server model.")
sub_head("TCP")
bp("TCP supplies logic to give a reliable connection-oriented protocol "
   "above IP. It provides a virtual circuit that two processes can use "
   "to communicate.")
sub_head("Internet addresses")
bp("In order to use a service, you must be able to find it. The Internet "
   "uses an address scheme for machines so that they can be located. "
   "The address is a 32 bit integer which gives the IP address. This "
   "encodes a network ID and more addressing. The network ID falls into "
   "various classes according to the size of the network address.")
bp("Class A uses 8 bits for the network address with 24 bits left over "
   "for other addressing. Class B uses 16 bit network addressing. "
   "Class C uses 24 bit network addressing and class D uses all 32.")
bp("Internally, the UNIX network is divided into sub networks. Building 11 "
   "is currently on one sub network and uses 10-bit addressing, allowing "
   "1024 different hosts. 8 bits are finally used for host addresses "
   "within our subnet. This places a limit of 256 machines that can be "
   "on the subnet. The 32 bit address is usually written as 4 integers "
   "separated by dots.")
sub_head("Port addresses")
bp("A service exists on a host, and is identified by its port. This is a "
   "16 bit number. To send a message to a server, you send it to the "
   "port for that service of the host that it is running on. This is not "
   "location transparency! Certain of these ports are 'well known'.")
sub_head("Sockets")
bp("A socket is a data structure maintained by the system to handle network "
   "connections. A socket is created using the call socket. It returns an "
   "integer that is like a file descriptor. In fact, under Windows, this "
   "handle can be used with ReadFile and WriteFile functions. Two processes "
   "wishing to communicate over a network create a socket each. These are "
   "similar to two ends of a pipe - but the actual pipe does not yet exist.")

sub_head("J2ME (Java 2 Micro Edition):-")
bp("Sun Microsystems defines J2ME as 'a highly optimized Java run-time "
   "environment targeting a wide range of consumer products, including pagers, "
   "cellular phones, screen-phones, digital set-top boxes and car navigation "
   "systems.' Announced in June 1999 at the JavaOne Developer Conference, "
   "J2ME brings the cross-platform functionality of the Java language to "
   "smaller devices, allowing mobile wireless devices to share applications. "
   "With J2ME, Sun has adapted the Java platform for consumer products that "
   "incorporate or are based on small computing devices.")
bp("J2ME uses configurations and profiles to customize the Java Runtime "
   "Environment (JRE). As a complete JRE, J2ME is comprised of a "
   "configuration, which determines the JVM used, and a profile, which "
   "defines the application by adding domain-specific classes. The "
   "configuration defines the basic run-time environment as a set of core "
   "classes and a specific JVM that run on specific types of devices.")

sub_head("Configurations overview")
bp("The configuration defines the basic run-time environment as a set of "
   "core classes and a specific JVM that run on specific types of devices. "
   "Currently, two configurations exist for J2ME:")
bullet("Connected Limited Device Configuration (CLDC): is used specifically "
       "with the KVM for 16-bit or 32-bit devices with limited amounts of "
       "memory. This is the configuration used for developing small J2ME "
       "applications. CLDC is also the configuration that we will use for "
       "developing our drawing tool application.")
bullet("Connected Device Configuration (CDC): is used with the C virtual "
       "machine (CVM) and is used for 32-bit architectures requiring more "
       "than 2 MB of memory. An example of such a device is a Net TV box.")

sub_head("Developing J2ME Applications")
bp("In this section, we will go over some considerations you need to keep "
   "in mind when developing applications for smaller devices. We'll take "
   "a look at the way the compiler is invoked when using J2SE to compile "
   "J2ME applications. Finally, we'll explore packaging and deployment and "
   "the role preverification plays in this process.")
bp("Developing applications for small devices requires you to keep certain "
   "strategies in mind during the design phase. It is best to strategically "
   "design an application for a small device before you begin coding. "
   "Correcting the code because you failed to consider all of the 'gotchas' "
   "before developing the application can be a painful process. Here are "
   "some design strategies to consider:")
bullet("Keep it simple. Remove unnecessary features, possibly making those "
       "features a separate, secondary application.")
bullet("Smaller is better. Smaller applications use less memory on the "
       "device and require shorter installation times. Consider packaging "
       "your Java applications as compressed Java Archive (jar) files.")
bullet("Minimize run-time memory use. To minimize the amount of memory used "
       "at run time, use scalar types in place of object types. Also, do not "
       "depend on the garbage collector. You should manage the memory "
       "efficiently yourself by setting object references to null when you "
       "are finished with them.")

sub_head("J2ME profiles")
bp("A profile defines the type of device supported. The Mobile Information "
   "Device Profile (MIDP), for example, defines classes for cellular phones. "
   "It adds domain-specific classes to the J2ME configuration to define uses "
   "for similar devices. Two profiles have been defined for J2ME and are "
   "built upon CLDC: KJava and MIDP. Both KJava and MIDP are associated with "
   "CLDC and smaller devices. Profiles are built on top of configurations.")
bp("KJava is Sun's proprietary profile and contains the KJava API. The KJava "
   "profile is built on top of the CLDC configuration. The KJava virtual "
   "machine, KVM, accepts the same byte codes and class file format as the "
   "classic J2SE virtual machine. KJava contains a Sun-specific API that "
   "runs on the Palm OS.")
bp("MIDP is geared toward mobile devices such as cellular phones and pagers. "
   "The MIDP, like KJava, is built upon CLDC and provides a standard run-time "
   "environment that allows new applications and services to be deployed "
   "dynamically on end user devices. MIDP is a common, industry-standard "
   "profile for mobile devices that is not dependent on a specific vendor. "
   "MIDP contains the following packages:")
for pkg in ["java.lang","java.io","java.util","javax.microedition.io",
            "javax.microedition.lcdui","javax.microedition.midlet",
            "javax.microedition.rms"]:
    bullet(pkg)

# ══════════════════════════════════════════════════════════════
# CH 5 – J2EE SOFTWARE ENVIRONMENT (FULL CONTENT)
# ══════════════════════════════════════════════════════════════
pb()
sec_head("J2EE Software Environment", 14)

sub_head("Client Server")
bp("With the varied topic in existence in the fields of computers, Client "
   "Server is one, which has generated more heat than light, and also more "
   "hype than reality. This technology has acquired a certain critical mass "
   "attention with its dedication conferences and magazines. Major computer "
   "vendors such as IBM and DEC, have declared that Client Servers is their "
   "main future market. A survey of DBMS magazine revealed that 76% of its "
   "readers were actively looking at the client server solution.")
bp("Client server implementations are complex but the underlying concept is "
   "simple and powerful. A client is an application running with local "
   "resources but able to request the database and related services from "
   "separate remote server. The software mediating this client server "
   "interaction is often referred to as MIDDLEWARE. The typical client either "
   "a PC or a Work Station connected through a network to a more powerful "
   "PC, Workstation, Midrange or Main Frames server usually capable of "
   "handling request from more than one client.")
bp("The key client server idea is that client as user is essentially insulated "
   "from the physical location and formats of the data needs for their "
   "application. With the proper middleware, a client input form or report "
   "can transparently access and manipulate both local database on the client "
   "machine and remote databases on one or more servers. An added bonus is "
   "the client server opens the door to multi-vendor database access including "
   "heterogeneous table joins.")

sub_head("What is a Client Server")
bp("Two prominent systems in existence are client server and file server "
   "systems. It is essential to distinguish between client servers and file "
   "server systems. Both provide shared network access to data but the "
   "comparison ends there! The file server simply provides a remote disk "
   "drive that can be accessed by LAN applications on a file by file basis. "
   "The client server offers full relational database services such as "
   "SQL-Access, Record modifying, Insert, Delete with full relational "
   "integrity backup/restore performance for high volume of transactions. "
   "The client server middleware provides a flexible interface between client "
   "and server, who does what, when and to whom.")

sub_head("Why Client Server")
bp("Client server has evolved to solve a problem that has been around since "
   "the earliest days of computing: how best to distribute your computing, "
   "data generation and data storage resources in order to obtain efficient, "
   "cost effective departmental and enterprise wide data processing. During "
   "mainframe era choices were quite limited. A central machine housed both "
   "the CPU and DATA (cards, tapes, drums and later disks). Access to these "
   "resources was initially confined to batched runs that produced "
   "departmental reports at the appropriate intervals. A strong central "
   "information service department ruled the corporation. The role of the "
   "rest of the corporation was limited to requesting new or more frequent "
   "reports and to provide hand written forms from which the central data "
   "banks were created and updated. The earliest client server solutions "
   "therefore could best be characterized as 'SLAVE-MASTER'.")
bp("Time-sharing changed the picture. Remote terminals could view and even "
   "change the central data, subject to access permissions. And, as the "
   "central data banks evolved into sophisticated relational databases with "
   "non-programmer query languages, online users could formulate adhoc "
   "queries and produce local reports without adding to the MIS applications "
   "software backlog. However remote access was through dumb terminals, and "
   "the client server remained subordinate to the Slave-Master architecture.")

sub_head("Front End or User Interface Design")
bp("The entire user interface is planned to be developed in browser specific "
   "environment with a touch of Intranet-Based Architecture for achieving the "
   "Distributed Concept. The browser specific components are designed by using "
   "the HTML standards, and the dynamism of the design is achieved by "
   "concentrating on the constructs of the Java Server Pages.")

sub_head("Communication or Database Connectivity Tier")
bp("The Communication architecture is designed by concentrating on the "
   "Standards of Servlets and Enterprise Java Beans. The database connectivity "
   "is established by using the Java Data Base Connectivity. The standards of "
   "three-tier architecture are given major concentration to keep the standards "
   "of higher cohesion and limited coupling for effectiveness of the operations.")

sub_head("Features of The Language Used")
bp("In my project, I have chosen Java language for developing the code. "
   "Initially the language was called as 'oak' but it was renamed as 'Java' "
   "in 1995. The primary motivation of this language was the need for a "
   "platform-independent (i.e., architecture neutral) language that could be "
   "used to create software to be embedded in various consumer electronic devices.")
bullet("Java is a programmer's language.")
bullet("Java is cohesive and consistent.")
bullet("Except for those constraints imposed by the Internet environment, "
       "Java gives the programmer, full control.")

sub_head("Importance of Java to the Internet")
bp("Java has had a profound effect on the Internet. This is because; Java "
   "expands the Universe of objects that can move about freely in Cyberspace. "
   "In a network, two categories of objects are transmitted between the Server "
   "and the Personal computer. They are: Passive information and Dynamic "
   "active programs. The Dynamic, Self-executing programs cause serious "
   "problems in the areas of Security and probability. But, Java addresses "
   "those concerns and by doing so, has opened the door to an exciting new "
   "form of program called the Applet.")
bp("Java can be used to create two types of programs – Applications and Applets. "
   "An application is a program that runs on our Computer under the operating "
   "system of that computer. An Applet is an application designed to be "
   "transmitted over the Internet and executed by a Java-compatible web browser. "
   "An applet is actually a tiny Java program, dynamically downloaded across "
   "the network, just like an image. But the difference is, it is an intelligent "
   "program, not just a media file. It can react to the user input and "
   "dynamically change.")

sub_head("Features Of Java")
bp("Security: Every time you download a 'normal' program, you are risking a "
   "viral infection. Java answers both these concerns by providing a 'firewall' "
   "between a network application and your computer. When you use a "
   "Java-compatible Web browser, you can safely download Java applets without "
   "fear of virus infection or malicious intent.")
bp("Portability: For programs to be dynamically downloaded to all the various "
   "types of platforms connected to the Internet, some means of generating "
   "portable executable code is needed. The same mechanism that helps ensure "
   "security also helps create portability. Java's solution to these two "
   "problems is both elegant and efficient.")
bp("The Byte Code: The key that allows Java to solve the security and "
   "portability problems is that the output of Java compiler is Byte code. "
   "Byte code is a highly optimized set of instructions designed to be "
   "executed by the Java run-time system, which is called the Java Virtual "
   "Machine (JVM). Translating a Java program into byte code helps makes it "
   "much easier to run a program in a wide variety of environments.")

sub_head("Java Architecture")
bp("Java architecture provides a portable, robust, high performing "
   "environment for development. Java provides portability by compiling "
   "the byte codes for the Java Virtual Machine, which is then interpreted "
   "on each platform by the run-time environment. Java is a dynamic system, "
   "able to load code when needed from a machine in the same room or across "
   "the planet.")
bp("When you compile the code, the Java compiler creates machine code "
   "(called byte code) for a hypothetical machine called Java Virtual "
   "Machine (JVM). The JVM is supposed to execute the byte code. The JVM "
   "is created for overcoming the issue of portability. The code is written "
   "and compiled for one machine and interpreted on all machines.")
bp("During run-time the Java interpreter tricks the byte code file into "
   "thinking that it is running on a Java Virtual Machine. In reality this "
   "could be an Intel Pentium Windows 95 or Sun SPARC station running "
   "Solaris or Apple Macintosh running system and all could receive code "
   "from any computer through Internet and run the Applets.")
bp("Java was designed to be easy for the professional programmer to learn "
   "and to use effectively. Java is strictly typed; it checks your code at "
   "compile time and run time. Java virtually eliminates the problems of "
   "memory management and deallocation, which is completely automatic. "
   "In a well-written Java program, all run time errors can and should be "
   "managed by your program.")

sub_head("Why Client Server")
bp("Client server has evolved to solve a problem that has been around since "
   "the earliest days of computing: how best to distribute your computing, "
   "data generation and data storage resources in order to obtain efficient, "
   "cost effective departmental and enterprise wide data processing. During "
   "the mainframe era choices were quite limited. A central machine housed "
   "both the CPU and DATA. Access to these resources was initially confined "
   "to batched runs that produced departmental reports at appropriate "
   "intervals. The role of the rest of the corporation was limited to "
   "requesting new or more frequent reports. The earliest client server "
   "solutions could best be characterized as 'SLAVE-MASTER'.")
bp("Time-sharing changed the picture. Remote terminals could view and even "
   "change the central data, subject to access permissions. As the central "
   "data banks evolved into sophisticated relational databases with "
   "non-programmer query languages, online users could formulate ad-hoc "
   "queries and produce local reports. However remote access was through "
   "dumb terminals, and the client server remained subordinate to the "
   "Slave-Master architecture.")

sub_head("JAVASCRIPT")
bp("JavaScript is a script-based programming language that was developed by "
   "Netscape Communication Corporation. JavaScript was originally called Live "
   "Script and renamed as JavaScript to indicate its relationship with Java. "
   "JavaScript supports the development of both client and server components "
   "of Web-based applications. On the client side, it can be used to write "
   "programs that are executed by a Web browser within the context of a Web "
   "page. On the server side, it can be used to write Web server programs "
   "that can process information submitted by a Web browser and then update "
   "the browser's display accordingly.")
bp("JavaScript statements can be included in HTML documents by enclosing the "
   "statements between a pair of scripting tags. Here are a few things we "
   "can do with JavaScript:")
bullet("Validate the contents of a form and make calculations.")
bullet("Add scrolling or changing messages to the Browser's status line.")
bullet("Animate images or rotate images that change when we move the mouse over them.")
bullet("Detect the browser in use and display different content for different browsers.")
bullet("Detect installed plug-ins and notify the user if a plug-in is required.")
bp("JavaScript and Java are entirely different languages. Java applets are "
   "generally displayed in a box within the web document; JavaScript can "
   "affect any part of the Web document itself. While JavaScript is best "
   "suited to simple applications and adding interactive features to Web "
   "pages; Java can be used for incredibly complex applications.")

sub_head("Hyper Text Markup Language")
bp("Hypertext Markup Language (HTML), the language of the World Wide Web "
   "(WWW), allows users to produce Web pages that include text, graphics and "
   "pointers to other Web pages (Hyperlinks). HTML is not a programming "
   "language but it is an application of ISO Standard 8879, SGML (Standard "
   "Generalized Markup Language), but specialized to hypertext and adapted "
   "to the Web. The idea behind Hypertext is that instead of reading text in "
   "rigid linear structure, we can easily jump from one point to another "
   "point. We can navigate through the information based on our interest and "
   "preference. A markup language is simply a series of elements, each "
   "delimited with special characters that define how text or other items "
   "enclosed within the elements should be displayed.")
bp("HTML can be used to display any type of document on the host computer, "
   "which can be geographically at a different location. It is a versatile "
   "language and can be used on any platform or desktop. HTML provides tags "
   "(special codes) to make the document look attractive. HTML tags are not "
   "case-sensitive. Using graphics, fonts, different sizes, color, etc., "
   "can enhance the presentation of the document. Anything that is not a "
   "tag is part of the document itself.")

sub_head("Basic HTML Tags:")
for tag, desc in [
    ("<!--  -->",           "Specifies comments"),
    ("<A>…</A>",            "Creates hypertext links"),
    ("<B>…</B>",            "Formats text as bold"),
    ("<BIG>…</BIG>",        "Formats text in large font"),
    ("<BODY>…</BODY>",      "Contains all tags and text in the HTML document"),
    ("<CENTER>…</CENTER>",  "Creates centered text"),
    ("<FONT>…</FONT>",      "Formats text with a particular font"),
    ("<FORM>…</FORM>",      "Encloses a fill-out form"),
    ("<H#>…</H#>",          "Creates headings of different levels"),
    ("<HEAD>…</HEAD>",      "Contains tags that specify information about a document"),
    ("<HTML>…</HTML>",      "Contains all other HTML tags"),
    ("<SCRIPT>…</SCRIPT>",  "Contains client-side or server-side script"),
    ("<TABLE>…</TABLE>",    "Creates a table"),
    ("<TD>…</TD>",          "Indicates table data in a table"),
    ("<TR>…</TR>",          "Designates a table row"),
]:
    bullet(f"{tag}  -  {desc}")

sub_head("Java Database Connectivity")
bp("JDBC is a Java API for executing SQL statements. JDBC is often thought "
   "of as standing for Java Database Connectivity. It consists of a set of "
   "classes and interfaces written in the Java programming language. JDBC "
   "provides a standard API for tool/database developers and makes it "
   "possible to write database applications using a pure Java API. Using "
   "JDBC, it is easy to send SQL statements to virtually any relational "
   "database. The combinations of Java and JDBC lets a programmer write it "
   "once and run it anywhere.")
bp("Simply put, JDBC makes it possible to do three things:")
bullet("Establish a connection with a database")
bullet("Send SQL statements")
bullet("Process the results")
bp("The JDBC drivers that we are aware of at this time fit into one of four "
   "categories:")
bullet("JDBC-ODBC bridge plus ODBC driver")
bullet("Native-API partly-Java driver")
bullet("JDBC-Net pure Java driver")
bullet("Native-protocol pure Java driver")
bp("In the two-tier model, a Java applet or application talks directly to "
   "the database. This requires a JDBC driver that can communicate with the "
   "particular database management system being accessed. A user's SQL "
   "statements are delivered to the database, and the results of those "
   "statements are sent back to the user. The database may be located on "
   "another machine to which the user is connected via a network. This is "
   "referred to as a client/server configuration.")
bp("In the three-tier model, commands are sent to a 'middle tier' of services, "
   "which then send SQL statements to the database. The database processes "
   "the SQL statements and sends the results back to the middle tier, which "
   "then sends them to the user. MIS directors find the three-tier model "
   "very attractive because the middle tier makes it possible to maintain "
   "control over access and the kinds of updates that can be made to "
   "corporate data.")

sub_head("Java Server Pages (JSP)")
bp("Java Server Pages is a simple, yet powerful technology for creating and "
   "maintaining dynamic-content web pages. Based on the Java programming "
   "language, Java Server Pages offers proven portability, open standards, "
   "and a mature re-usable component model. The Java Server Pages "
   "architecture enables the separation of content generation from content "
   "presentation. This separation not only eases maintenance headaches, it "
   "also allows web team members to focus on their areas of expertise.")
bp("Features of JSP:")
bp("Portability: Java Server Pages files can be run on any web server or "
   "web-enabled application server that provides support for them. Dubbed "
   "the JSP engine, this support involves recognition, translation, and "
   "management of the Java Server Page lifecycle and its interaction components.")
bp("Components: The Java Server Pages architecture can include reusable Java "
   "components. The architecture also allows for the embedding of a scripting "
   "language directly into the Java Server Pages file. The components current "
   "supported include Java Beans, and Servlets.")
bp("Processing: A Java Server Pages file is essentially an HTML document with "
   "JSP scripting or tags. Before the page is served, the Java Server Pages "
   "syntax is parsed and processed into a Servlet on the server side. The "
   "Servlet that is generated outputs real content in straight HTML for "
   "responding to the client.")
bp("Steps in the execution of a JSP Application:")
num_bullet("The client sends a request to the web server for a JSP file by giving "
           "the name of the JSP file within the form tag of a HTML page.")
num_bullet("This request is transferred to the JavaWebServer. At the server side "
           "JavaWebServer receives the request and if it is a request for a jsp "
           "file, server gives this request to the JSP engine.")
num_bullet("JSP engine is a program which can understand the tags of the jsp and "
           "then it converts those tags into a Servlet program and it is stored "
           "at the server side.")

sub_head("JDBC Connectivity")
bp("The JDBC provides database-independent connectivity between the J2EE "
   "platform and a wide range of tabular data sources. JDBC technology "
   "allows an Application Component Provider to:")
bullet("Perform connection and authentication to a database server")
bullet("Manage transactions")
bullet("Move SQL statements to a database engine for preprocessing and execution")
bullet("Execute stored procedures")
bullet("Inspect and modify the results from Select statements")

sub_head("Tomcat 6.0 Web Server")
bp("Tomcat is an open source web server developed by Apache Group. Apache "
   "Tomcat is the servlet container that is used in the official Reference "
   "Implementation for the Java Servlet and Java Server Pages technologies. "
   "The Java Servlet and Java Server Pages specifications are developed by "
   "Sun under the Java Community Process. Web Servers like Apache Tomcat "
   "support only web components while an application server supports web "
   "components as well as business components (BEAs Weblogic, is one of the "
   "popular application servers). To develop a web application with "
   "jsp/servlet install any web server like JRun, Tomcat etc. to run your application.")

sub_head("Bibliography:")
bp("References for the Project Development were taken from the following "
   "Books and Web Sites.")
sub_head("Oracle")
bullet("PL/SQL Programming by Scott Urman")
bullet("SQL Complete Reference by Livion")
sub_head("JAVA Technologies")
bullet("JAVA Complete Reference")
bullet("Java Script Programming by Yehuda Shiran")
bullet("Mastering JAVA Security")
bullet("JAVA2 Networking by Pistoria")
bullet("JAVA Security by Scott Oaks")
bullet("Head First EJB Sierra Bates")
bullet("J2EE Professional by Shadab Siddiqui")
bullet("JAVA Server Pages by Larne Pekowsley")
bullet("JAVA Server Pages by Nick Todd")
sub_head("HTML")
bullet("HTML Black Book by Holzner")
sub_head("JDBC")
bullet("Java Database Programming with JDBC by Patel Moss")
bullet("Software Engineering by Roger Pressman")
sub_head("Blockchain & IoT")
bullet("Cosmos SDK Documentation – Cosmos Network")
bullet("XACML Version 3.0 Specification – OASIS Open Standard")
bullet("Social Internet of Things – Springer, 2020")
bullet("Blockchain Technology and Applications – IEEE Press")
bullet("Internet of Educational Things – ACM Computing Surveys, 2023")

# ══════════════════════════════════════════════════════════════
# CH 6 – ARCHITECTURE CLASS DIAGRAM
# ══════════════════════════════════════════════════════════════
pb()
sec_head("ARCHITECTURE CLASS DIAGRAM", 14)

sub_head("-   Architecture Diagram :")
bp("The EducationalSIoT platform is implemented as an application-specific "
   "blockchain using the Cosmos SDK. The platform consists of four main "
   "modules: Device Management Module (DMM), Social Management Module (SMM), "
   "Academic Service Module (ASM), and Access Control Module (ACM). The "
   "architecture diagram below shows how these modules interact and how "
   "IoET devices connect through the blockchain to exchange academic services "
   "with enforced social-aware access control.")
img("/tmp/orig_imgs/p1_img1.png", 14,
    "Fig.1: Blockchain-based Educational Social Internet of Things Platform Architecture")

sub_head("EducationalSIoT Platform Architecture Details")
bp("The EducationalSIoT platform is built on the Cosmos SDK, which is an "
   "application-specific blockchain framework. Unlike general-purpose "
   "blockchains such as Ethereum, the application-specific blockchain "
   "allows custom modules to be implemented directly as part of the "
   "blockchain logic. This eliminates the limitations of smart contracts "
   "and allows the platform to incorporate complex business logic including "
   "machine learning models for EIOT device classification.")
bp("The platform architecture consists of two main layers:")
bullet("Blockchain Layer: The Cosmos SDK-based blockchain that provides "
       "the distributed, tamper-proof foundation. All modules (DMM, SMM, "
       "ASM, ACM) are implemented as blockchain modules. All transactions "
       "are stored in blocks and distributed across multiple nodes.")
bullet("Application Layer: The Java/J2EE web application that provides "
       "the user interface for Admin and User interactions. It communicates "
       "with the blockchain layer through REST APIs.")
bp("The blockchain nodes in the EducationalSIoT network are the IoET "
   "devices themselves. Each smart device that registers with the "
   "platform can act as a blockchain node, contributing to the "
   "distributed consensus. This peer-to-peer architecture eliminates "
   "the need for a central server and ensures the availability and "
   "resilience of the platform.")

pb()
sub_head("-   Class Diagram :")
bp("The Social XACML-based Access Policy Model is the core of the "
   "EducationalSIoT authorization mechanism. The class diagram represents "
   "the hierarchical structure of the policy model: an AccessPolicySet "
   "contains multiple AccessPolicy objects, each containing multiple "
   "AccessRule objects. Each AccessRule is associated with a Target that "
   "specifies the subjects, resources, and actions it applies to, an Effect "
   "(Permit or Deny), a Priority value, ContextualConditions (device "
   "attributes), and SocialConditions (social relationship type, contact "
   "frequency, and contact duration). The SocialCondition class distinguishes "
   "between ClsOR (Class Object Relationship) and InsOR (Institution Object "
   "Relationship) to adapt access control to the educational context.")
img("/tmp/orig_imgs/cropped_class_diagram_orig.png", 14,
    "Fig.2: Class Diagram – Social XACML Access Policy Model")

sub_head("XACML Policy Model Classes Description")
bp("The Social XACML-based Access Policy Model consists of the following "
   "classes:")

sub_head("AccessPolicySet")
bp("The AccessPolicySet is the top-level element of the policy model. It "
   "contains a collection of AccessPolicy objects and defines the combining "
   "algorithm that is used to combine the decisions from the individual "
   "policies. In the EducationalSIoT platform, the combining algorithm is "
   "either 'permit-overrides' (Permit if any policy permits) or "
   "'deny-overrides' (Deny if any policy denies). Each AccessPolicySet has "
   "a unique label, a target, and a priority value.")

sub_head("AccessPolicy")
bp("The AccessPolicy is a collection of AccessRule objects. It defines the "
   "combining algorithm for its rules. An AccessPolicy has a unique label, "
   "a target that specifies the subjects, resources, and actions it applies "
   "to, a combining algorithm, and a priority value. The target of an "
   "AccessPolicy narrows down the set of requests to which the policy applies.")

sub_head("AccessRule")
bp("The AccessRule is the basic unit of the policy model. It contains:")
bullet("Target: Specifies the conditions under which the rule applies. "
       "The target includes subject attributes (device type, trust degree, "
       "interest similarity, centrality), resource attributes (service type), "
       "and action attributes (read, write, execute).")
bullet("Effect: The decision that the rule produces if it applies and its "
       "conditions are satisfied. The effect is either 'Permit' or 'Deny'.")
bullet("Priority: An integer value that indicates the priority of the rule. "
       "Higher priority rules are evaluated first in the priority-based "
       "combining algorithm.")
bullet("ContextualCondition: A list of conditions based on device attributes "
       "such as minimum trust degree, minimum interest similarity, minimum "
       "centrality, and service type.")
bullet("SocialCondition: A list of conditions based on social relationship "
       "features such as relationship type (ClsOR/InsOR), minimum contact "
       "frequency, minimum contact duration, and friendship period.")

sub_head("SocialCondition Class")
bp("The SocialCondition class is the key extension of the standard XACML "
   "model for the EducationalSIoT platform. It captures social relationship "
   "constraints that cannot be expressed in standard XACML. A SocialCondition "
   "specifies:")
bullet("RelationshipTypeList: The list of acceptable social relationship "
       "types (ClsOR, InsOR, or both).")
bullet("MinContactFrequency: The minimum number of contacts required between "
       "the requesting device and the target device.")
bullet("MinContactDuration: The minimum total duration (in minutes) of "
       "contacts between the devices.")
bullet("FriendshipPeriod: The validity period during which the social "
       "relationship is considered active.")

sub_head("Priority-Based Combining Algorithms")
bp("The EducationalSIoT platform introduces two new priority-based combining "
   "algorithms for the XACML policy model:")
bullet("Priority-Permit-Overrides: Evaluates rules in order of decreasing "
       "priority. Returns Permit as soon as a high-priority Permit rule "
       "is satisfied. This algorithm is used in emergency situations where "
       "a high-priority device should be granted access even if lower-priority "
       "rules deny it.")
bullet("Priority-Deny-Overrides: Evaluates rules in order of decreasing "
       "priority. Returns Deny as soon as a high-priority Deny rule is "
       "satisfied. This algorithm is used in security-critical resources "
       "where a high-priority denial should block access regardless of "
       "lower-priority permit rules.")

# ══════════════════════════════════════════════════════════════
# CH 7 – MODULES
# ══════════════════════════════════════════════════════════════
pb()
sec_head("Modules", 14)

sub_head("Admin (Service Provider)")
bp("In this module, the Admin has to login by using a valid user name and "
   "password. After login is successful he can perform the following operations: "
   "Login, View All End Users and Authorize, View All Datasets, Access and "
   "View All EIOT Device Datasets by Blockchain, View EIOT Device Results, "
   "View E-learning Board Type Results, View Institution Type Results, and "
   "View Education Level Type Results.")

sub_head("View and Authorize Users")
bp("In this module, the admin can view the list of users who all registered. "
   "In this, the admin can view the user's details such as user name, email, "
   "address and admin authorizes the users.")

sub_head("User (Remote User)")
bp("In this module, there are n numbers of users present. User should register "
   "before doing any operations. Once user registers, their details will be "
   "stored to the database. After registration is successful, he has to login "
   "by using authorized user name and password. Once Login is successful user "
   "will do the following operations: Register and Login, My Profile, "
   "Upload Datasets, View All Upload Datasets, Find EIOT Device Type Results, "
   "Find EIOT Device Type Results By Blockchain.")

sub_head("Device Management Module (DMM)")
bp("The Device Management Module handles the registration and management of "
   "IoET devices on the EducationalSIoT blockchain platform. Each IoET device "
   "is registered with its attributes including device type (e.g. smart "
   "whiteboard, laptop, smart glasses), owner identity, location, and "
   "capabilities. The DMM ensures that only authorized devices are permitted "
   "to join the network and exchange academic services. Device attributes "
   "managed by DMM include: device identifier, device type, device category, "
   "e-learning board type, institution type, and education level.")

sub_head("Social Management Module (SMM)")
bp("The Social Management Module manages the social relationships between "
   "IoET devices. The SMM implements two new types of educational social "
   "relationships: Class Object Relationship (ClsOR) and Institution Object "
   "Relationship (InsOR). ClsOR is established between devices of the same "
   "class session (e.g. instructor's laptop and student tablets in the same "
   "classroom). InsOR is established between devices belonging to the same "
   "institution. The SMM tracks social features such as contact frequency, "
   "contact duration, and social similarity scores, which are used by the "
   "Access Control Module during policy evaluation.")

sub_head("Academic Service Module (ASM)")
bp("The Academic Service Module manages the academic services that can be "
   "exchanged between IoET devices on the platform. Academic services include "
   "sharing lecture materials, streaming instructional videos, accessing "
   "e-learning boards, and providing accessibility assistance for students "
   "with disabilities. The ASM ensures that service requests are properly "
   "routed to the Access Control Module for authorization before any service "
   "is provided to a requesting device.")

sub_head("Access Control Module (ACM)")
bp("The Access Control Module is the security core of the EducationalSIoT "
   "platform. It implements the social XACML-based authorization mechanism "
   "that controls access to academic services. The ACM consists of the "
   "following components:")
bullet("Policy Enforcement Point (PEP): Intercepts all access requests from "
       "IoET devices and forwards them to the PDP for evaluation. Enforces "
       "the access decision returned by the PDP.")
bullet("Policy Decision Point (PDP): Evaluates the access request against "
       "the applicable XACML policies. Uses contextual information and "
       "social relationship data to make an access decision.")
bullet("Policy Administration Point (PAP): Manages the lifecycle of XACML "
       "access control policies stored on the blockchain. Allows authorized "
       "administrators to create, update, and delete policies.")
bullet("Policy Information Point (PIP): Provides the PDP with the current "
       "attribute values of the requesting device and the requested resource. "
       "Retrieves data from the DMM and SMM as needed.")
bp("The ACM also manages the delegation of access permissions. When a device "
   "is unable to directly access a service, it can request delegation from "
   "another device that has the required permissions. The delegation process "
   "is governed by delegation policies that specify the social constraints "
   "for delegation operations. The delegation request evaluation time is "
   "0.32ms, ensuring real-time performance.")

sub_head("Module Interaction")
bp("The four modules of the EducationalSIoT platform interact as follows: "
   "When an IoET device registers with the platform, the DMM stores its "
   "attributes on the blockchain. As the device interacts with other devices, "
   "the SMM records social relationships (ClsOR and InsOR) and tracks "
   "social features such as contact frequency and duration. When the device "
   "requests access to an academic service through the ASM, the ACM "
   "retrieves the applicable policies from the PAP, queries the DMM and SMM "
   "for contextual and social information, evaluates the policy, and returns "
   "a Permit or Deny decision. The entire process is transparent, "
   "decentralized, and tamper-proof due to the blockchain foundation.")

sub_head("Database Tables")
bp("The following database tables are used in the EducationalSIoT platform "
   "to store user data, device information, datasets, and results:")

sub_head("User Table")
bp("The User table stores the registration details of all users in the system:")
bullet("UserId: Auto-increment primary key for each user record.")
bullet("UserName: The full name of the registered user.")
bullet("Email: The email address of the user (unique identifier).")
bullet("Password: The encrypted password for authentication.")
bullet("Address: The physical address of the user.")
bullet("Status: Authorization status (Pending/Authorized/Revoked).")
bullet("RegisterDate: The date and time the user registered.")

sub_head("Dataset Table")
bp("The Dataset table stores information about uploaded EIOT device datasets:")
bullet("DatasetId: Auto-increment primary key for each dataset.")
bullet("UserId: Foreign key referencing the User table.")
bullet("DatasetName: The name of the uploaded dataset file.")
bullet("DatasetPath: The server path where the dataset is stored.")
bullet("UploadDate: The date and time the dataset was uploaded.")
bullet("Status: Processing status (Uploaded/Processing/Processed).")

sub_head("EIOT Device Table")
bp("The EIOT Device table stores the classification results for EIOT devices:")
bullet("DeviceId: Auto-increment primary key.")
bullet("DatasetId: Foreign key referencing the Dataset table.")
bullet("DeviceType: The classified type of the IoET device.")
bullet("ELearningBoardType: The e-learning board type classification.")
bullet("InstitutionType: The institution type classification.")
bullet("EducationLevel: The education level classification.")
bullet("BlockchainHash: The blockchain transaction hash for verification.")
bullet("ProcessDate: The date and time the classification was performed.")

sub_head("Admin Table")
bp("The Admin table stores the credentials of system administrators:")
bullet("AdminId: Auto-increment primary key.")
bullet("AdminName: The full name of the administrator.")
bullet("Email: The email address (unique identifier).")
bullet("Password: The encrypted password for authentication.")
bullet("LastLogin: The date and time of the last login.")

# ══════════════════════════════════════════════════════════════
# CH 8 – DATA FLOW DIAGRAM
# ══════════════════════════════════════════════════════════════
pb()
sec_head("Data Flow Diagram", 14)
bp("A Data Flow Diagram (DFD) is a graphical representation of the flow of "
   "data through an information system. It models the processes (or "
   "functions) that transform the data, and shows the data stores, data "
   "flows, and external entities. DFDs are used to visualize the processing "
   "of data in a system. They help in representing the logical flow of data "
   "without representing the physical characteristics. A DFD shows how the "
   "system will operate, how the data will move, and where the data will be "
   "stored in the system. There are different levels of DFDs:")
bullet("Level 0 DFD (Context Diagram): The top level DFD showing the entire "
       "system as a single process with inputs and outputs.")
bullet("Level 1 DFD: Breaks down the single process from Level 0 into major "
       "sub-processes.")
bullet("Level 2 DFD: Further breaks down each process from Level 1 into "
       "more detailed sub-processes.")
bp("The DFD below illustrates the complete data flow for the Blockchain-based "
   "EducationalSIoT platform, from the IoET device sending an access request "
   "to the final authorization decision being returned by the blockchain.")
img("/tmp/orig_imgs/cropped_dfd_orig.png", 14,
    "Fig.3: Data Flow Diagram – Blockchain-based EducationalSIoT Platform")

sub_head("Level 0 DFD – Context Diagram")
bp("The Level 0 DFD (Context Diagram) represents the entire "
   "Blockchain-based EducationalSIoT system as a single process. "
   "The external entities that interact with the system are:")
bullet("Admin (Service Provider): The administrator who manages the system, "
       "authorizes users, views datasets, and monitors the blockchain results.")
bullet("User (Remote User): The end user who registers, uploads datasets, "
       "and queries EIOT device results through the blockchain.")
bullet("IoET Devices: The Internet of Educational Things devices (smart "
       "whiteboards, laptops, tablets, smart glasses) that register with "
       "the platform and request access to academic services.")
bp("The main inputs to the system are: Admin login credentials, user "
   "registration data, EIOT device datasets, access policy requests, "
   "and social relationship data. The main outputs from the system are: "
   "Authorization decisions, EIOT device classification results, "
   "e-learning board type results, institution type results, and "
   "education level type results.")

sub_head("Level 1 DFD – Main Processes")
bp("The Level 1 DFD breaks down the system into its major processes. "
   "The main processes identified in the Blockchain-based EducationalSIoT "
   "platform are:")
num_bullet("User/Admin Authentication Process: Handles the login of both "
           "Admin and User. Validates credentials against the User Database "
           "and creates a session for authorized users.")
num_bullet("User Registration Process: Allows new users to register in "
           "the system. Stores user details including name, email, address "
           "and other profile information in the User Database.")
num_bullet("Dataset Upload and Management Process: Allows users to upload "
           "EIOT device datasets. Stores the datasets in the Dataset Store "
           "for further processing by the blockchain engine.")
num_bullet("Blockchain-based Access Evaluation Process: The core process "
           "that evaluates access requests against XACML policies. "
           "Interacts with the Policy Store, Device Management data, "
           "and Social Graph to make authorization decisions.")
num_bullet("EIOT Device Result Processing: Classifies and processes EIOT "
           "device datasets to determine device type, e-learning board type, "
           "institution type, and education level.")
num_bullet("Social Relationship Management Process: Manages ClsOR and InsOR "
           "social relationships between IoET devices. Updates the Social "
           "Graph Store with contact frequency, duration, and similarity scores.")

sub_head("Data Stores")
bp("The following data stores are used in the Blockchain-based EducationalSIoT platform:")
bullet("User Database: Stores user registration details, login credentials, "
       "and authorization status.")
bullet("Dataset Store: Stores all uploaded EIOT device datasets submitted "
       "by users for blockchain-based classification.")
bullet("Policy Store (PAP): Stores all XACML access control policies "
       "including AccessPolicySets, AccessPolicies, and AccessRules with "
       "social conditions.")
bullet("Social Graph Store: Stores the social relationships between IoET "
       "devices including ClsOR, InsOR, contact frequency, contact duration, "
       "and social similarity scores.")
bullet("Blockchain Ledger: The immutable distributed ledger that stores "
       "all transactions, access decisions, and EIOT device classification "
       "results for audit and accountability.")
bullet("Results Store: Stores the computed results for EIOT device type, "
       "e-learning board type, institution type, and education level "
       "classification for display to Admin and User.")

sub_head("DFD Level 2 – Blockchain Access Evaluation Process")
bp("The Level 2 DFD for the Blockchain Access Evaluation Process (Process 3 "
   "from Level 1) breaks down into the following sub-processes:")
num_bullet("Receive Access Request: The PEP receives the access request "
           "from the IoET device and extracts the subject, resource, "
           "and action information.")
num_bullet("Retrieve Policy: The PDP queries the PAP on the blockchain to "
           "retrieve the applicable AccessPolicySets and AccessPolicies "
           "for the requested resource.")
num_bullet("Retrieve Device Attributes: The PDP queries the PIP for the "
           "current attribute values of the requesting device from the "
           "Device Management Module.")
num_bullet("Retrieve Social Data: The PDP queries the Social Management "
           "Module for the social relationship type, contact frequency, "
           "and contact duration between the requesting device and the "
           "target resource device.")
num_bullet("Evaluate Policy: The PDP evaluates all applicable AccessRules "
           "against the retrieved contextual information and social data. "
           "The priority-based combining algorithm is applied to produce "
           "a final access decision.")
num_bullet("Log Transaction: The access decision is logged as a transaction "
           "on the blockchain for audit and accountability purposes.")
num_bullet("Return Decision: The access decision (Permit/Deny) and any "
           "obligations are returned to the PEP for enforcement.")

sub_head("Social Relationships in the DFD")
bp("The Social Relationship Management Process (Process 6 from Level 1) "
   "is responsible for tracking and updating the social features between "
   "IoET devices. This process:")
bullet("Monitors all interactions between IoET devices and records the "
       "frequency and duration of their contacts.")
bullet("Classifies social relationships as ClsOR (Class Object Relationship) "
       "when two devices are active in the same class session.")
bullet("Classifies social relationships as InsOR (Institution Object "
       "Relationship) when two devices belong to the same institution.")
bullet("Computes social similarity scores based on shared services, "
       "common social connections, and interaction patterns.")
bullet("Updates the Social Graph Store with the current social features "
       "after each device interaction event.")
bullet("Provides the current social relationship data to the PDP when "
       "queried during the policy evaluation process.")

# ══════════════════════════════════════════════════════════════
# CH 9 – USE CASE DIAGRAM
# ══════════════════════════════════════════════════════════════
pb()
sec_head("Use Case Diagram", 14)
bp("A Use Case Diagram models the interactions between users (actors) and "
   "the system to achieve a specific goal. It captures the functional "
   "requirements of a system. A use case diagram shows the system as a "
   "black box and shows how the system interacts with external entities "
   "(actors). The notation used in a use case diagram consists of: "
   "Actors (represented as stick figures), Use Cases (represented as "
   "ellipses), System Boundary (a rectangle enclosing use cases), and "
   "Relationships (lines connecting actors to use cases).")
bp("The diagram below shows the two main actors in the EducationalSIoT "
   "platform: the Admin (Service Provider) and the User (Remote User), "
   "along with their respective use cases. The system boundary encloses "
   "all the use cases supported by the platform.")
img("/tmp/orig_imgs/cropped_usecase_orig.png", 14,
    "Fig.4: Use Case Diagram – Blockchain-based EducationalSIoT Platform")

sub_head("Actors")
bp("The following actors have been identified in the Blockchain-based "
   "EducationalSIoT platform:")
bullet("Admin (Service Provider): The administrator who is responsible for "
       "managing the entire system. The Admin has privileges to view and "
       "authorize users, view datasets, and access blockchain-based results.")
bullet("User (Remote User): The end user who interacts with the system to "
       "upload datasets and view results. Users must register and be "
       "authorized by the Admin before accessing full system capabilities.")

sub_head("Admin Use Cases")
bp("The following use cases apply to the Admin actor:")
for uc in [
    "Login: The Admin enters valid credentials (username and password) to "
    "access the system dashboard.",
    "View All End Users and Authorize: The Admin views the list of all "
    "registered users and authorizes them to use the system.",
    "View All Datasets: The Admin views all datasets uploaded by users "
    "in the system.",
    "Access and View All EIOT Device Datasets By Blockchain: The Admin "
    "uses the blockchain mechanism to access and view EIOT device datasets "
    "with guaranteed data integrity.",
    "View EIOT Device Results: The Admin views the classification results "
    "for EIOT device types.",
    "View E-learning Board Type Results: The Admin views the classification "
    "results for e-learning board types.",
    "View Institution Type Results: The Admin views the classification "
    "results for institution types.",
    "View Education Level Type Results: The Admin views the classification "
    "results for education levels.",
]:
    bullet(uc)

sub_head("User Use Cases")
bp("The following use cases apply to the User actor:")
for uc in [
    "Register: A new user registers in the system by providing personal "
    "details including name, email, and address.",
    "Login: The registered and authorized user logs into the system using "
    "valid credentials.",
    "My Profile: The user views and updates their profile information.",
    "Upload Datasets: The user uploads EIOT device datasets for processing "
    "and classification.",
    "View All Upload Datasets: The user views all datasets they have "
    "previously uploaded to the system.",
    "Find EIOT Device Type Results: The user queries the system to find "
    "EIOT device type classification results for their uploaded datasets.",
    "Find EIOT Device Type Results By Blockchain: The user uses the "
    "blockchain mechanism to find EIOT device type results with "
    "verifiable data integrity.",
]:
    bullet(uc)

sub_head("Use Case Relationships")
bp("The use cases in the system have the following relationships:")
bullet("Include Relationship: The 'Login' use case is included in both "
       "'View All End Users and Authorize' and 'Upload Datasets' use cases, "
       "as authentication is required before performing any operation.")
bullet("Extend Relationship: 'Find EIOT Device Type Results By Blockchain' "
       "extends 'Find EIOT Device Type Results' by providing an additional "
       "blockchain-based verification layer.")
bullet("Generalization: Both Admin and User generalize from a base 'System "
       "User' actor in terms of login functionality.")

# ══════════════════════════════════════════════════════════════
# CH 10 – SEQUENCE DIAGRAM
# ══════════════════════════════════════════════════════════════
pb()
sec_head("Sequence Diagram", 14)
bp("A Sequence Diagram is an interaction diagram that describes how objects "
   "interact in a particular sequence of messages over time. It represents "
   "the objects involved in the interaction and the messages they exchange "
   "in the sequence of their occurrence. Sequence diagrams are used to "
   "model the dynamic aspects of a system. They are used to describe the "
   "behavior of the system in terms of objects and messages.")
bp("The key elements of a sequence diagram include:")
bullet("Lifeline: A vertical dashed line representing the existence of an "
       "object or component during the interaction.")
bullet("Activation Bar: A rectangle on the lifeline that represents the "
       "period during which an object is performing an action.")
bullet("Message: A horizontal arrow between lifelines representing the "
       "communication between objects.")
bullet("Return Message: A dashed arrow representing the return value from "
       "a called operation.")
bp("The sequence diagram below illustrates the complete authorization flow "
   "in the EducationalSIoT platform from an IoT device requesting access "
   "to an academic service through the social XACML-based policy evaluation.")
img("/tmp/orig_imgs/cropped_sequence_orig.png", 14,
    "Fig.5: Sequence Diagram – Authorization Mechanism")

sub_head("Detailed Step-by-Step Authorization Flow")
bp("The complete authorization flow in the Blockchain-based EducationalSIoT "
   "platform consists of the following steps:")

num_bullet("Request Access: The IoT Device (requesting device) sends an "
           "access request to the Policy Enforcement Point (PEP). The request "
           "contains the subject identifier (device ID), the resource being "
           "requested (academic service), and the action (e.g. read, write).")
num_bullet("Forward Request: The PEP receives the access request and forwards "
           "it to the Channel Handler (CH). The PEP acts as the enforcement "
           "point that will ultimately allow or deny access based on the "
           "decision it receives.")
num_bullet("Route to PDP: The Channel Handler routes the request to the "
           "Policy Decision Point (PDP). The CH is responsible for managing "
           "the communication channel between the PEP and the PDP.")
num_bullet("Query Policy Administration Point (PAP): The PDP queries the "
           "PAP to retrieve the applicable access policies (AccessPolicySets) "
           "for the requested resource. The PAP stores all XACML policies "
           "on the blockchain.")
num_bullet("Extract Access Policy Set: The PAP returns the applicable "
           "AccessPolicySet to the PDP. This includes all the AccessPolicies "
           "and AccessRules that need to be evaluated.")
num_bullet("Query Policy Information Point (PIP): The PDP queries the "
           "PIP to retrieve the current attribute values of the requesting "
           "device and the requested resource. These include device type, "
           "trust degree, interest similarity, and centrality values.")
num_bullet("Retrieve Contextual Information: The PIP returns the contextual "
           "information to the PDP. This data is used to evaluate the "
           "ContextualConditions specified in the AccessRules.")
num_bullet("Query Device Management Module (DMM): The PDP queries the "
           "DMM to verify the registration status and device attributes "
           "of the requesting IoET device. The DMM confirms whether the "
           "device is a registered and authorized device on the platform.")
num_bullet("Query Social Management Module (SMM): The PDP queries the "
           "SMM for social relationship data between the requesting device "
           "and the target resource. The SMM provides: social relationship "
           "type (ClsOR or InsOR), minimum contact frequency, minimum "
           "contact duration, and social activeness.")
num_bullet("Evaluate Social XACML Policy: The PDP evaluates the XACML "
           "policies using the retrieved contextual information, device "
           "attributes, and social relationship data. The evaluation applies "
           "the priority-based combining algorithms to produce a final "
           "access decision.")
num_bullet("Access Decision: The PDP produces an access decision of "
           "Permit or Deny. If Permit, the requesting device is granted "
           "access to the academic service. If Deny, access is refused.")
num_bullet("Obligations: The PDP also returns obligations that must be "
           "fulfilled before the access is granted. These may include "
           "logging the access event on the blockchain, notifying the "
           "resource owner, or limiting the scope of access.")
num_bullet("Return Decision through Channel: The access decision and "
           "obligations are returned to the PEP through the Channel Handler.")
num_bullet("Enforce Decision: The PEP enforces the access decision. If "
           "Permit, the IoT Device is allowed to access the requested "
           "academic service. If Deny, the request is blocked.")
num_bullet("Return Result: The PEP returns the result of the access request "
           "to the requesting IoT Device. The entire authorization evaluation "
           "completes in 0.22ms.")

sub_head("Performance Evaluation")
bp("The simulation results of the authorization mechanism show that the "
   "EducationalSIoT platform achieves excellent performance. The average "
   "access request evaluation time is 0.22ms, which ensures real-time "
   "authorization for IoET devices. The delegation request evaluation time "
   "is 0.32ms. These results demonstrate that the integration of social "
   "features into the XACML policy model does not significantly impact "
   "the performance of the authorization mechanism.")
bp("The performance breakdown by phase is as follows:")
bullet("Policy retrieval from PAP (Steps 4-5): ~0.05ms")
bullet("Attribute retrieval from PIP (Steps 6-7): ~0.04ms")
bullet("Device verification from DMM (Step 8): ~0.03ms")
bullet("Social relationship retrieval from SMM (Step 9): ~0.06ms")
bullet("Policy evaluation by PDP (Step 10): ~0.04ms")
bp("The EducationalSIoT platform ensures that the authorization mechanism "
   "is both secure and efficient, making it suitable for deployment in "
   "real educational institutions with large numbers of IoET devices.")

sub_head("Security Analysis")
bp("The EducationalSIoT platform is designed to be secure against common "
   "attacks. The security mechanisms implemented include:")
bullet("Man-in-the-Middle Attack Prevention: All communications between "
       "the components are encrypted using TLS/SSL. The blockchain ensures "
       "that all policies and transactions are digitally signed and "
       "tamper-proof.")
bullet("Replay Attack Prevention: Each access request includes a timestamp "
       "and a nonce. The PDP verifies that the request has not been "
       "previously processed, preventing replay attacks.")
bullet("Denial of Service Prevention: The rate limiting mechanism in the "
       "Channel Handler prevents any single device from flooding the "
       "system with access requests.")
bullet("Policy Tampering Prevention: All XACML policies are stored on "
       "the blockchain and cannot be modified without consensus from "
       "the network nodes.")

# ══════════════════════════════════════════════════════════════
# CH 11 – FLOW CHART DIAGRAM
# ══════════════════════════════════════════════════════════════
pb()
sec_head("Flow Chart Diagram", 14)
bp("A flowchart is a type of diagram that represents an algorithm, workflow "
   "or process. The flowchart shows the steps as boxes of various kinds, "
   "and their order by connecting the boxes with arrows. Flowcharts are "
   "used to design, document, manage and communicate complex processes "
   "or programs in various fields. They are particularly useful in software "
   "engineering to represent program logic in a visual format.")
bp("The standard flowchart symbols used are:")
bullet("Oval/Rounded Rectangle (Terminator): Represents the start or end "
       "of the flowchart.")
bullet("Rectangle (Process): Represents a process, action, or operation.")
bullet("Diamond (Decision): Represents a decision point with two or more "
       "possible outcomes (Yes/No).")
bullet("Parallelogram (Input/Output): Represents input or output operations.")
bullet("Arrow (Flow Line): Represents the direction of flow or connection "
       "between steps.")
bp("The flowcharts below show the detailed operational flow for the Admin "
   "(Service Provider) module and the User (Remote User) module of the "
   "EducationalSIoT platform.")

sub_head("-   Flow Chart : Admin")
img("/tmp/orig_imgs/cropped_flowchart_admin_orig.png", 9,
    "Fig.6: Flow Chart – Admin Module")
sub_head("Admin Module Flow Description")
bp("The Admin (Service Provider) module flow is as follows:")
num_bullet("Start: The Admin opens the EducationalSIoT application in "
           "a web browser.")
num_bullet("Enter Credentials: The Admin enters the username and password "
           "on the login page.")
num_bullet("Validate Credentials: The system checks the entered credentials "
           "against the Admin database. If the credentials are invalid, "
           "an error message is displayed and the Admin is redirected back "
           "to the login page.")
num_bullet("Login Successful: If the credentials are valid, the Admin is "
           "taken to the Admin Dashboard.")
num_bullet("Admin Dashboard: The Admin can perform the following operations "
           "from the dashboard:")
bp("   a. View All End Users and Authorize: The Admin views the list of "
   "all registered users and can authorize or revoke authorization for "
   "each user.")
bp("   b. View All Datasets: The Admin views all datasets uploaded by "
   "all users in the system.")
bp("   c. Access and View All EIOT Device Datasets By Blockchain: The "
   "Admin accesses the blockchain-stored EIOT device datasets for "
   "integrity-verified viewing.")
bp("   d. View EIOT Device Results: The Admin views the classification "
   "results for EIOT device types for all submitted datasets.")
bp("   e. View E-learning Board Type Results: The Admin views the "
   "classification results for e-learning board types.")
bp("   f. View Institution Type Results: The Admin views the "
   "classification results for educational institution types.")
bp("   g. View Education Level Type Results: The Admin views the "
   "classification results for education level types.")
num_bullet("Logout: The Admin can logout from the system at any time, "
           "which terminates the session and redirects to the login page.")
num_bullet("End: The flowchart terminates when the Admin logs out.")

pb()
sub_head("-   Flow Chart : User")
img("/tmp/orig_imgs/cropped_flowchart_user_orig.png", 9,
    "Fig.7: Flow Chart – User Module")
sub_head("User Module Flow Description")
bp("The User (Remote User) module flow is as follows:")
num_bullet("Start: The User opens the EducationalSIoT application in a "
           "web browser.")
num_bullet("New User Check: The system checks if the user is a new user "
           "or an existing user.")
num_bullet("Registration (New User): If the user is new, they fill in the "
           "registration form with their details (name, email, address, "
           "password) and submit it.")
num_bullet("Authorization Pending: After registration, the user account "
           "is created but the user must wait for the Admin to authorize "
           "their account.")
num_bullet("Login: Once authorized, the User enters their username and "
           "password to log in.")
num_bullet("Validate Credentials: The system validates the credentials. "
           "If invalid, an error message is shown and the user is "
           "redirected to login.")
num_bullet("Login Successful: If the credentials are valid and the account "
           "is authorized, the User is taken to the User Dashboard.")
num_bullet("User Dashboard: The User can perform the following operations:")
bp("   a. My Profile: The User views and updates their personal profile "
   "information.")
bp("   b. Upload Datasets: The User uploads EIOT device datasets to the "
   "system for processing and classification.")
bp("   c. View All Upload Datasets: The User views all datasets they "
   "have previously uploaded.")
bp("   d. Find EIOT Device Type Results: The User queries the system to "
   "find classification results for their uploaded EIOT device datasets.")
bp("   e. Find EIOT Device Type Results By Blockchain: The User uses the "
   "blockchain mechanism to retrieve classification results with "
   "guaranteed data integrity and tamper-proof verification.")
num_bullet("Logout: The User can logout from the system at any time.")
num_bullet("End: The flowchart terminates when the User logs out.")

# ══════════════════════════════════════════════════════════════
# CH 12 – SYSTEM TESTING
# ══════════════════════════════════════════════════════════════
pb()
sec_head("SYSTEM TESTING", 14)

sub_head("TESTING METHODOLOGIES")
bp("The following are the Testing Methodologies:")
for tm in ["Unit Testing.","Integration Testing.","User Acceptance Testing.",
           "Output Testing.","Validation Testing."]:
    bullet(tm)

sub_head("Unit Testing")
bp("Unit testing focuses verification effort on the smallest unit of Software "
   "design – the module. Unit testing exercises specific paths in a module's "
   "control structure to ensure complete coverage and maximum error detection. "
   "This test focuses on each module individually, ensuring that it functions "
   "properly as a unit. Hence, the naming is Unit Testing.")
bp("During this testing, each module is tested individually and the module "
   "interfaces are verified for the consistency with design specification. "
   "All important processing paths are tested for the expected results. "
   "All error handling paths are also tested.")

sub_head("Integration Testing")
bp("Integration testing addresses the issues associated with the dual problems "
   "of verification and program construction. After the software has been "
   "integrated a set of high order tests are conducted. The main objective "
   "in this testing process is to take unit tested modules and build a program "
   "structure that has been dictated by design.")
bp("The following are the types of Integration Testing:")

sub_head("1.  Top Down Integration")
bp("This method is an incremental approach to the construction of program "
   "structure. Modules are integrated by moving downward through the control "
   "hierarchy, beginning with the main program module. The module subordinates "
   "to the main program module are incorporated into the structure in either "
   "a depth first or breadth first manner.")
bp("In this method, the software is tested from main module and individual "
   "stubs are replaced when the test proceeds downwards.")

sub_head("2.  Bottom-up Integration")
bp("This method begins the construction and testing with the modules at the "
   "lowest level in the program structure. Since the modules are integrated "
   "from the bottom up, processing required for modules subordinate to a "
   "given level is always available and the need for stubs is eliminated. "
   "The bottom up integration strategy may be implemented with the "
   "following steps:")
bullet("The low-level modules are combined into clusters that perform a "
       "specific Software sub-function.")
bullet("A driver (i.e.) the control program for testing is written to "
       "coordinate test case input and output.")
bullet("The cluster is tested.")
bullet("Drivers are removed and clusters are combined moving upward in "
       "the program structure.")

sub_head("User Acceptance Testing")
bp("User Acceptance of a system is the key factor for the success of any "
   "system. The system under consideration is tested for user acceptance by "
   "constantly keeping in touch with the prospective system users at the "
   "time of developing and making changes wherever required. The system "
   "developed provides a friendly user interface that can easily be "
   "understood even by a person who is new to the system.")

sub_head("Output Testing")
bp("After performing the validation testing, the next step is output testing "
   "of the proposed system, since no system could be useful if it does not "
   "produce the required output in the specified format. Asking the users "
   "about the format required by them tests the outputs generated or displayed "
   "by the system under consideration. Hence the output format is considered "
   "in 2 ways – one is on screen and another in printed format.")

sub_head("Validation Checking")
bp("Validation checks are performed on the following fields.")
sub_head("Text Field:")
bp("The text field can contain only the number of characters lesser than or "
   "equal to its size. The text fields are alphanumeric in some tables and "
   "alphabetic in other tables. Incorrect entry always flashes an error message.")
sub_head("Numeric Field:")
bp("The numeric field can contain only numbers from 0 to 9. An entry of any "
   "character flashes an error message. The individual modules are checked "
   "for accuracy and what it has to perform. Each module is subjected to a "
   "test run along with sample data. The individually tested modules are "
   "integrated into a single system. Testing involves executing the real "
   "data information used in the program; the existence of any program "
   "defect is inferred from the output. The testing should be planned so "
   "that all the requirements are individually tested.")
bp("A successful test is one that gives out the defects for the inappropriate "
   "data and produces an output revealing the errors in the system.")

sub_head("Preparation of Test Data")
bp("Taking various kinds of test data does the above testing. Preparation of "
   "test data plays a vital role in the system testing. After preparing the "
   "test data the system under study is tested using that test data. While "
   "testing the system by using test data errors are again uncovered and "
   "corrected by using above testing steps and corrections are also noted "
   "for future use.")

sub_head("Using Live Test Data:")
bp("Live test data are those that are actually extracted from organization "
   "files. After a system is partially constructed, programmers or analysts "
   "often ask users to key in a set of data from their normal activities. "
   "Then, the systems person uses this data as a way to partially test the "
   "system. In other instances, programmers or analysts extract a set of "
   "live data from the files and have them entered themselves.")
bp("It is difficult to obtain live data in sufficient amounts to conduct "
   "extensive testing. And, although it is realistic data that will show how "
   "the system will perform for the typical processing requirement, assuming "
   "that the live data entered are in fact typical, such data generally will "
   "not test all combinations or formats that can enter the system. This bias "
   "toward typical values then does not provide a true systems test and in "
   "fact ignores the cases most likely to cause system failure.")

sub_head("Using Artificial Test Data:")
bp("Artificial test data are created solely for test purposes, since they "
   "can be generated to test all combinations of formats and values. In "
   "other words, the artificial data, which can quickly be prepared by a "
   "data generating utility program in the information systems department, "
   "make possible the testing of all login and control paths through the "
   "program. The most effective test programs use artificial test data "
   "generated by persons other than those who wrote the programs. Often, "
   "an independent team of testers formulates a testing plan, using the "
   "systems specifications.")
bp("The package 'Blockchain-based Authorization Mechanism for Educational "
   "Social Internet of Things' has satisfied all the requirements specified "
   "as per software requirement specification and was accepted.")

sub_head("USER TRAINING")
bp("Whenever a new system is developed, user training is required to educate "
   "them about the working of the system so that it can be put to efficient "
   "use by those for whom the system has been primarily designed. For this "
   "purpose the normal working of the project was demonstrated to the "
   "prospective users. Its working is easily understandable and since the "
   "expected users are people who have good knowledge of computers, the use "
   "of this system is very easy.")

sub_head("MAINTENANCE")
bp("This covers a wide range of activities including correcting code and "
   "design errors. To reduce the need for maintenance in the long run, we "
   "have more accurately defined the user's requirements during the process "
   "of system development. Depending on the requirements, this system has "
   "been developed to satisfy the needs to the largest possible extent. "
   "With development in technology, it may be possible to add many more "
   "features based on the requirements in future. The coding and designing "
   "is simple and easy to understand which will make maintenance easier.")

sub_head("TESTING STRATEGY:")
bp("A strategy for system testing integrates system test cases and design "
   "techniques into a well-planned series of steps that results in the "
   "successful construction of software. The testing strategy must co-operate "
   "test planning, test case design, test execution, and the resultant data "
   "collection and evaluation. A strategy for software testing must "
   "accommodate low-level tests that are necessary to verify that a small "
   "source code segment has been correctly implemented as well as high level "
   "tests that validate major system functions against user requirements.")
bp("Software testing is a critical element of software quality assurance and "
   "represents the ultimate review of specification design and coding. "
   "Testing represents an interesting anomaly for the software. Thus, a "
   "series of testing are performed for the proposed system before the "
   "system is ready for user acceptance testing.")

sub_head("SYSTEM TESTING:")
bp("Software once validated must be combined with other system elements "
   "(e.g. Hardware, people, database). System testing verifies that all the "
   "elements are proper and that overall system function performance is "
   "achieved. It also tests to find discrepancies between the system and "
   "its original objective, current specifications and system documentation.")

sub_head("UNIT TESTING:")
bp("In unit testing different modules are tested against the specifications "
   "produced during the design for the modules. Unit testing is essential "
   "for verification of the code produced during the coding phase, and hence "
   "the goals are to test the internal logic of the modules. Using the "
   "detailed design description as a guide, important control paths are "
   "tested to uncover errors within the boundary of the modules. This "
   "testing is carried out during the programming stage itself. In this "
   "type of testing step, each module was found to be working satisfactorily "
   "as regards to the expected output from the module.")

sub_head("White Box Testing")
bp("White Box Testing is a testing technique that examines the program "
   "structure and derives test data from the program logic and code. "
   "The tester knows the internal design, code and implementation. "
   "In this type of testing, the structure of the code is tested. "
   "White box testing is used to test the following:")
bullet("Statement Coverage: Every statement in the code is executed at "
       "least once during the testing.")
bullet("Branch Coverage: Every branch of each decision point is tested "
       "at least once.")
bullet("Path Coverage: Every independent path through the code is tested "
       "at least once.")
bullet("Condition Coverage: Every condition in every decision point is "
       "tested for both true and false outcomes.")
bp("White box testing was applied to all modules of the EducationalSIoT "
   "platform including the XACML policy evaluation engine, the blockchain "
   "transaction processing, and the social relationship management algorithms. "
   "All test cases were designed to cover the critical paths and boundary "
   "conditions of the access control decision logic.")

sub_head("Black Box Testing")
bp("Black Box Testing is a testing technique that does not use any "
   "information about the internal implementation. The tester only knows "
   "the inputs and expected outputs. This type of testing focuses on the "
   "functional requirements of the software. The following types of black "
   "box testing were performed on the EducationalSIoT platform:")
bullet("Equivalence Partitioning: Input data was divided into partitions "
       "of valid and invalid data. One test case was designed for each "
       "partition.")
bullet("Boundary Value Analysis: Test cases were designed for the boundary "
       "values of each input field.")
bullet("Error Guessing: Test cases were designed based on past experience "
       "with similar systems to catch common errors.")
bullet("Cause-Effect Graphing: Relationships between inputs and outputs "
       "were modeled to design test cases that cover all cause-effect "
       "combinations.")
bp("In Due Course, latest technology advancements will be taken into "
   "consideration. As part of technical build-up many components of the "
   "networking system will be generic in nature so that future projects can "
   "either use or interact with this. The future holds a lot to offer to "
   "the development and refinement of this project.")

# ══════════════════════════════════════════════════════════════
# CH 13 – CONCLUSION
# ══════════════════════════════════════════════════════════════
pb()
sec_head("CONCLUSION", 14)
bp("In this paper, we propose an Educational Social Internet of Things "
   "(EducationalSIoT) platform to provide academic services based on the "
   "social network of IoET devices. Our EducationalSIoT platform leverages "
   "the class and the institution social relationships to efficiently provide "
   "academic services for different stakeholders such as teachers, "
   "administration staff and students, in particular students with disabilities.")
bp("To secure the exchanged data and information, we incorporate the social "
   "conditions in the XACML policy model. We extend the XACML authorization "
   "mechanism by adjusting the policy evaluation process and proposing new "
   "rule-based and policy-based combining algorithms. Furthermore, the access "
   "permissions can be guaranteed by delegation operations. Thus, the social "
   "constraints are integrated in the access permission delegation process "
   "in order to control the delegation operation.")
bp("The simulation results show that the processing times for policy evaluation "
   "and request evaluation ensures the scalability and performance of our "
   "access control mechanism. By integrating social features, an access "
   "request is evaluated in 0.22ms and a delegation request is evaluated in "
   "0.32ms. Additionally, we ensure the confidentiality and integrity of "
   "data provided by the academic services and the security of our "
   "EducationalSIoT platform against the man-in-the-middle and replay attacks.")
bp("As a future work, we suggest extending our EducationalSIoT platform by "
   "adding more services such as the smart disability assistance services "
   "in order to incorporate students with disabilities into the learning "
   "process. Moreover, we plan to integrate the social features to perform "
   "indirect delegation operations based on the Friend of A Friend (FoAF) "
   "social relationships.")

# ══════════════════════════════════════════════════════════════
# CH 14 – REFERENCES
# ══════════════════════════════════════════════════════════════
pb()
sec_head("REFERENCES", 14)
refs = [
    "[1] K. Polin, T. Yigitcanlar, M. Limb and T. Washington., 'The Making of Smart Campus: A Review and Conceptual Framework,' Buildings, vol. 13, no. 4, 2023. DOI: 10.3390/buildings13040891.",
    "[2] O. Diaz-Parra et al., 'Smart Education and future trends,' Int. Journal of COP and Infor., vol. 13, no. 1, pp. 65-74, Jan. 2022.",
    "[3] A.A. Mawgoud, M.H.N. Taha and N.E.M. Khalifa, 'Security Threats of Social Internet of Things in the Higher Education Environment,' Toward Social Internet of Things (SIoT), Springer, 2019, pp. 151-171.",
    "[4] M. Al-Emran, S.I. Malik and M.N. Al-Kabi, 'A Survey of Internet of Things (IoT) in Education: Opportunities and Challenges,' Toward Social Internet of Things (SIoT), Springer, 2020, pp. 197-209.",
    "[5] L.E. Holmquist et al., 'Smart-Its Friends: A Technique for Users to Easily Establish Connections between Smart Artefacts,' Ubicomp 2001, Berlin, Germany, 2001, pp. 116-122.",
    "[6] L. Atzori, A. Iera and G. Morabito, 'SIoT: Giving a Social Structure to the Internet of Things,' IEEE Communications Letters, vol. 15, no. 11, pp. 1193-1195, Nov. 2011.",
    "[7] A. Zamanifar, 'Social IoT Healthcare,' in Toward Social Internet of Things (SIoT), Springer, 2020, pp. 1-11.",
    "[8] J. Chandra Priya, R.N. Karthika, K. Suresh Kumar, and P. Valarmathie, 'BlockSIoT: a Blockchain-Based Secure Data Sharing in SIoT,' in Proceedings of Data Analytics and Management: ICDAM 2021, 2022, pp. 687-700.",
    "[9] S. Kumar and A. Vidhate, 'Issues and Future Trends in IoT Security using Blockchain: A Review,' in IDCIoT, Bengaluru, India, 2023, pp. 976-984.",
    "[10] M. Khan and A. Malviya, 'Big data approach for sentiment analysis of twitter data using Hadoop framework and deep learning,' ic-ETITE, Vellore, India, 2020, pp. 1-5.",
    "[11] M. Khan et al., 'A deep learning approach for facial emotions recognition using principal component analysis and neural network techniques,' The Photogrammetric Record, vol. 37, no. 180, pp. 435-452, 2022.",
    "[12] O. Dallel, S. Ben Ayed and J. Bel Hadj Taher, 'Smart Blockchain-based Authorization for Social Internet of Things,' in CW2023, Sousse, Tunisia, 2023.",
    "[13] A. Badshah et al., 'Towards Smart Education through Internet of Things: A Survey,' ACM Comput. Surv., vol. 56, no. 2, pp. 1-33, Sep. 2023. DOI: 10.1145/3610401.",
    "[14] H.M. Knight, P.R. Gajendragadkar and A. Bokhari, 'Wearable technology: using Google Glass as a teaching tool,' Case Reports, Mai 2015.",
    "[15] L. Ting, M. Khan, A. Sharma and M. D. Ansari, 'A secure framework for IoT-based smart climate agriculture system,' Journal of Intelligent Systems, vol. 31, no. 1, pp. 221-236, 2022.",
    "[16] E. Rissanen, 'eXtensible Access Control Markup Language (XACML) Version 3.0,' OASIS Open, 2013.",
    "[17] J. Bernal Bernabe et al., 'SocIoTal - The Development and Architecture of a Social IoT framework,' in GIoTS, Geneva, Switzerland, 2017, pp. 1-6.",
    "[18] A. Mohamed et al., 'Extended Authorization Policy for Graph-Structured Data,' SN COMPUT. SCI., vol. 2, no. 351, 2021.",
    "[19] R. Abassi and S. Guemara El Fatmi, 'Delegation Management Modeling in a Security Policy based Environment,' International Symposium on Symbolic Computation in Software Science, 2013.",
    "[20] J. Kwon and E. Buchman, 'Cosmos Whitepaper: A Network of Distributed Ledgers,' Cosmos Network.",
    "[21] H. Zhang et al., 'Adaptive Fine-grained Access Control Method in Social Internet of Things,' International Journal of Network Security, vol. 23, no. 1, pp. 42-48, Jan. 2021.",
    "[22] J. Wu et al., 'A Fine-Grained Cross-Domain Access Control Mechanism for Social Internet of Things,' in IEEE 11th Intl Conf on UIC, Bali, Indonesia, 2014, pp. 666-671.",
    "[23] P. Chinnasamy et al., 'Smart Contract-Enabled Secure Sharing of Health Data for a Mobile Cloud-Based E-Health System,' Applied Sciences, vol. 13, no. 6, p.3970, 2023.",
    "[24] H. Saidi et al., 'DSMAC: Privacy-aware Decentralized Self-Management of data Access Control based on blockchain for health data,' IEEE Access, vol. 10, pp. 101011-101028, 2022.",
    "[25] L. Yunliang et al., 'Blockchain-based access control architecture for multi-domain environments,' Pervasive and Mobile Computing, vol. 98, pp. 101878, 2024.",
    "[26] A. Gauhar et al., 'xDBAuth: Blockchain based cross domain authentication and authorization framework for Internet of Things,' IEEE Access, vol. 8, pp. 58800-58816, 2020.",
    "[27] Geospatial eXtensible Access Control Markup Language (GeoXACML). Open Geospatial Consortium.",
    "[28] A. Ashutosh et al., 'XACML for Mobility (XACML4M): An Access Control Framework for Connected Vehicles,' Sensors, vol. 23, no. 4, 2023.",
]
for ref in refs:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(5)
    run(p, ref, False, 11)

# ── save ──────────────────────────────────────────────────────
out = "/tmp/Revuri_Nikitha_Project_FINAL_v2.docx"
doc.save(out)
import os
print(f"Saved: {out}  ({os.path.getsize(out)//1024} KB)")
