from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import os, os.path
from datetime import date
from numpy import NaN
import pandas as pd
from datetime import date, datetime
from msedge.selenium_tools import EdgeOptions
from msedge.selenium_tools import Edge
from werkzeug.utils import secure_filename
import uuid
import pathlib

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'csv'}


columnsToRemove = ["Permit Number", "Pending", "Date In", "Created in CEPS Date", "Assigned Date", "Entering Date", "Date Out", "Days Pending", "Days from Received to Created",
                    "Days from Created to Assigned", "Days from Received to Entering", "Days with MA", "Days with SA", "Days from Received to Issued", "Days Prcessing minus Pending Days", 
                    "Application Weight Factor", "Permit Weight Factor", "Created By", "Issued By", "Last Updated By", "Last Updated"]
columnOrder = ['Applicant', 'Application ID', 'Status', 'Purpose', 'Trade Type', 'Permit Type', 'Permit Usage', 'Days Old', 'Days Over Standard', 'Assigned To']

app = Flask(__name__)

app.secret_key = 'key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

path = pathlib.Path('uploads')
path.mkdir(parents=True, exist_ok=True)


def login(email, password):
    edge_options = EdgeOptions()
    edge_options.use_chromium = True  
    edge_options.add_argument('headless')
    edge_options.add_argument('disable-gpu')
    browser = Edge(executable_path='msedgedriver.exe', options=edge_options)

    browser.get('https://intranet.ec.gc.ca/citespermits/index.cfm?fuseaction=home.login&lang=E')

    browser.find_element_by_xpath('/html/body/div[2]/div/div[5]/div[2]/div/form[1]/table/tbody/tr[1]/td[2]/input[1]').send_keys(email)
    browser.find_element_by_xpath('/html/body/div[2]/div/div[5]/div[2]/div/form[1]/table/tbody/tr[2]/td[2]/input').send_keys(password)
    browser.find_element_by_xpath("/html/body/div[2]/div/div[5]/div[2]/div/form[1]/table/tbody/tr[3]/td[2]/input").click()

    return browser

def is_polar_bear(browser, app_id):
    browser.get('https://intranet.ec.gc.ca/citespermits/index.cfm?fuseaction=application.edit&tab=species&intApplicationID=' + app_id)
    text = browser.find_element_by_xpath('//*[@id="divShowSpeciesBlock"]/table[2]/tbody/tr[2]/td[2]').text

    if 'Polar bear' in text:
        return True
    else:
        return False

def get_applicant(browser, app_id):
    browser.get('https://intranet.ec.gc.ca/citespermits/index.cfm?fuseaction=application.edit&tab=addresses&intApplicationID=' + app_id)
    text = browser.find_element_by_xpath('//*[@id="divShowAddressBlock_1"]/fieldset/div/table/tbody/tr[2]/td[1]').text
    text = text.split('\n')

    applicant = ''

    for x in range(len(text)):
        if 'c/o' in text[x]:
            for y in range(x):
                applicant = applicant + " " + text[y]
    
    if applicant == '':
        applicant = text[0]

    return applicant.strip()

def generate_ceps_df():

    columnsToRemove = ["Permit Number", "Pending", "Purpose", "Trade Type", "Permit Usage", "Date In", "Created in CEPS Date", "Assigned Date", "Entering Date", "Date Out", "Days Pending", "Days from Received to Created",
                    "Days from Created to Assigned", "Days from Received to Entering", "Days with MA", "Days with SA", "Days from Received to Issued", "Days Prcessing minus Pending Days", 
                    "Application Weight Factor", "Permit Weight Factor", "Created By", "Issued By", "Last Updated By", "Last Updated"]

    # CSV Input File
    csvFile = session['file_location']

    df = pd.read_csv(csvFile)

    df = df.drop(df[df["Assigned To"].isin(["Jin Moon", "Sara Bauman", "Adel Ferjani", "Claudette Pion"]) == False].index)

    df = df.drop(df[df.Pending == "Yes"].index)

    df = df.drop(df[df.Status == "MA Approved"].index)

    df['Days Pending'] = df['Days Pending'].fillna(0)

    df['Date In'] = df['Date In'].astype('datetime64[ns]').dt.date

    df['Age'] = ((date.today() - df['Date In']).dt.days) - df['Days Pending']

    df.drop(columnsToRemove, inplace=True, axis=1)

    df = df.sort_values(['Assigned To', 'Status', 'Age'])

    df = df.sort_values(by=['Age'], ascending=False)

    df.columns = ['Application ID', 'Status', 'Permit Type', 'Assigned To', 'Age']

    df['color'] = None

    df = df.reset_index(drop=True)

    for index, row in df.iterrows():
        if row['Permit Type'] == 'Hunting Trophy':
            if row['Assigned To'] == 'Adel Ferjani':
                if row['Age'] >= 65: 
                    df.at[index, 'color'] = 'table-danger'
                elif row['Age'] >= 60 and row['Age'] < 65:
                    df.at[index, 'color'] = 'table-warning'
                else:
                    df.at[index, 'color'] = 'table-light'
            else:
                if row['Age'] >= 16: 
                    df.at[index, 'color'] = 'table-danger'
                elif row['Age'] >= 11 and row['Age'] < 16:
                    df.at[index, 'color'] = 'table-warning'
                else:
                    df.at[index, 'color'] = 'table-light'
        elif row['Permit Type'] == 'Animals' or row['Permit Type'] == 'Ginseng & Goldenseal' or row['Permit Type'] == 'Certificate of Ownership':
            if row['Age'] >= 30: 
                    df.at[index, 'color'] = 'table-danger'
            elif row['Age'] >= 25 and row['Age'] < 30:
                df.at[index, 'color'] = 'table-warning'
            elif row['Age'] <= 24:
               df.at[index, 'color'] = 'table-light'
        else:
            if row['Age'] >= 65: 
                    df.at[index, 'color'] = 'table-danger'
            elif row['Age'] >= 60 and row['Age'] < 65:
                df.at[index, 'color'] = 'table-warning'
            else:
                df.at[index, 'color'] = 'table-light'
            


    permit_officer_seperated = [df[df['Assigned To'] == 'Adel Ferjani'], df[df['Assigned To'] == 'Claudette Pion'], df[df['Assigned To'] == 'Sara Bauman'], df[df['Assigned To'] == 'Jin Moon']]

    list_of_permit_officers_apps = [permit_officer_seperated[0].values.tolist(), permit_officer_seperated[1].values.tolist(), permit_officer_seperated[2].values.tolist(), permit_officer_seperated[3].values.tolist()] 

    return list_of_permit_officers_apps


def assigned_to_df():
    columnsToRemove = ["Permit Number", "Pending", "Purpose", "Trade Type", "Permit Usage", "Date In", "Created in CEPS Date", "Assigned Date", "Entering Date", "Date Out", "Days Pending", "Days from Received to Created",
                    "Days from Created to Assigned", "Days from Received to Entering", "Days with MA", "Days with SA", "Days from Received to Issued", "Days Prcessing minus Pending Days", 
                    "Application Weight Factor", "Permit Weight Factor", "Created By", "Issued By", "Last Updated By", "Last Updated"]
    
    df = pd.read_csv(session['file_location'])

    df.drop(columnsToRemove, inplace=True, axis=1)

    df = df.drop(df[df["Assigned To"].isin(["Cecile Benoit", "Nasra Farah", "Permit Officer", "Hunting Trophy", NaN]) == False].index)

    df['Assigned To'] = df['Assigned To'].fillna('Blank')
    df = df.reset_index(drop=True)

    list_of_lists_df = df.values.tolist()

    return list_of_lists_df

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/home")
def hello_world():
    return render_template('home.jinja2')

@app.route("/")
def main_page():
    return render_template('to_upload.jinja2')

@app.route('/', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = str(uuid.uuid4()) + secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        session['file_location'] =  os.path.join(app.config['UPLOAD_FOLDER'], filename)

    return redirect(url_for('hello_world'))

@app.route('/print', methods=['GET'])
def print_func_get():
    return render_template('printing.jinja2') 

@app.route('/print', methods=['POST'])
def print_func():

    data = request.form
    print(data)

    browser = login(data['username'], data['password'])

    df = pd.read_csv(session['file_location'])

    df = df.drop(df[df["Status"].isin(["MA Approved"]) == False].index)
    df = df.drop(df[df.Pending == "Yes"].index)
    df['Date In'] = df['Date In'].astype('datetime64[ns]').dt.date
    df['Applicant'] = None
    df['Days Pending'].fillna(0, inplace=True)
    df = df.reset_index(drop=True)

    for index, row in df.iterrows():
        applicant = get_applicant(browser, str(row["Application ID"]))
        df.at[index, 'Applicant'] = applicant

        if row["Permit Type"] == 'Hunting Trophy' and row['Trade Type'] == 'Export':
            polar_bear = is_polar_bear(browser, str(row["Application ID"]))
            if polar_bear is True:
                df.at[index, 'Permit Weight Factor'] = 70
            else: 
                df.at[index, 'Permit Weight Factor'] = 21
        elif row["Permit Type"] == 'Scientific Certificate' or row["Permit Type"] == 'Injurious Wildlife':
            df.at[index, 'Permit Weight Factor'] = 70
        else:
            df.at[index, 'Permit Weight Factor'] = 35

    browser.quit()

    df['Days Old'] = ((date.today() - df['Date In']).dt.days) - df['Days Pending']
    df['Days Over Standard'] = df['Days Old'] - df['Permit Weight Factor']

    df.drop(columnsToRemove, inplace=True, axis=1)
    df = df[columnOrder]
    df = df.sort_values(by=['Days Over Standard'], ascending=False)

    df.to_excel('print_CEPS.xlsx', index=False)

    return send_file('print_CEPS.xlsx', as_attachment=True)
    
@app.route("/assigned")
def assigned():
    df_lists = assigned_to_df()
    total = len(df_lists)

    print(df_lists)
    return render_template('tobeassigned.jinja2', total=total, open_applications=df_lists)



@app.route("/open")
def open_apps():
    return render_template('open-pre.jinja2')

@app.route('/open', methods=['POST'])
def open_apps_post():
    po = request.form
    print(po)

    apps = generate_ceps_df()
    
    if po['permit-officer'] == 'Adel Ferjani':
        open_applications = apps[0]
    elif po['permit-officer'] == 'Claudette Pion':
        open_applications = apps[1]
    elif po['permit-officer'] == 'Sara Bauman':
        open_applications = apps[2]
    elif po['permit-officer'] == 'Jin Moon':
        open_applications = apps[3]

    proc = 0
    ma_review = 0
    sa_review = 0
    other = 0

    for x in range(len(open_applications)):
        if open_applications[x][1] == 'Entering' or open_applications[x][1] == 'Assigned':
            proc = proc+1
        elif open_applications[x][1] == 'MA Reviewing':
            ma_review = ma_review+1
        elif open_applications[x][1] == 'SA Reviewing':
            sa_review = sa_review+1
        elif open_applications[x][1] != 'SA Reviewing' and open_applications[x][1] != 'MA Reviewing' and open_applications[x][1] != 'Entering' and open_applications[x][1] != 'Assigned':
            other = other+1
    
    return render_template('open-post.jinja2', open_applications=open_applications, po=po['permit-officer'], total=len(open_applications), numbers=[proc, ma_review, sa_review, other])

if __name__ == '__main__':
    app.run(debug=True)