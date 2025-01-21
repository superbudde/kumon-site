from datetime import datetime, timedelta
import data_handle
import operator
from flask import Flask, render_template, request

app = Flask(__name__)

# AKA Student Database row amount
STUDENT_COUNT = 1000
FILE_EXTRACT_NAME = 'Student Database.xlsx'
SHEET_NAME = 'Tracker'

# Loop controlling program
loop = True

# Set up xlsx file
sheet = data_handle.data_collect(FILE_EXTRACT_NAME, SHEET_NAME)

# List containing students currently in the centre, with their times
students = []
html_students = []
# index, student name, time in, time out


@app.route('/')
def index():
    global html_students

    # Input from the text box
    index = request.args.get('student_index')
    # Save progress
    save_day()
    # Update the time left for students in centre
    for i in range(len(students)):
        html_index = find_student(students[i]["Index"])
        if html_index is not None:
            html_students[html_index]["Time Left"] = (
                student_time_remaining(students[i]["Index"], students[i]["Start Time"]))

    # If input received:
    if index is not None:
        try:
            # Try to log student in the centre
            index = int(index)
            if index <= STUDENT_COUNT:
                login_student(index)
                try:
                    html_students[len(html_students)-1]["Time Left"] = student_time_remaining(students[len(students)-1]["Index"], students[len(students)-1]["Start Time"])
                except IndexError:
                    print("Student removed")
                    return render_template('index.html', students=html_students)
            return render_template('index.html', students=html_students)
        except ValueError:
            return render_template('index.html', students=html_students)

    # if request.args.get('save') == "Save":
    #     save_day()

    return render_template('index.html', students=html_students)


def student_time_remaining(index, start_time):
    if sheet[get_student(index)][5] is not None:
        minutes_in_centre = int(sheet[get_student(index)][5])
        end_time = datetime.strptime(start_time, '%H:%M') + timedelta(minutes=minutes_in_centre)
        diff = end_time - datetime.strptime(datetime.now().strftime('%H:%M'), '%H:%M')
        if diff.total_seconds() < 0:
            return 0
        return int(diff.total_seconds())//60
    else:
        return 30


# Inputs the time the student entered/left the centre
def login_student(index):
    # Current time
    now = datetime.now()
    time = now.strftime("%H:%M")
    if get_student(index) is None:
        print("Index does not exist")
        return
    if sheet[get_student(index)][6] is None or sheet[get_student(index)][7] is None or sheet[get_student(index)][1] is None:
        return
    name = sheet[get_student(index)][6].split("(")[0] + " " + sheet[get_student(index)][7]
    type = sheet[get_student(index)][1]
    for i in range(len(students)):
        if students[i]["Index"] == index:
            try:
                if html_students[find_student(students[i]["Index"])]["Meeting"]:
                    html_students[find_student(students[i]["Index"])]["Meeting"] = False
                    return
            except:
                print("Out of range in html_students")
            hours_in, minutes_in = time_in_centre(index)
            students[i]["End Time"] = time

            # Remove student from html_students because they are logged out
            html_index = find_student(students[i]["Index"])
            if html_index is not None:
                html_students.pop(html_index)

            # Print time to user
            print("Student logged out at " + time)
            print(name, "was in the centre for", hours_in, "hours and", minutes_in, "minutes")
            return

    meeting = False
    if sheet[get_student(index)][8] == "Y" or sheet[get_student(index)][8] == "y":
        meeting = True
    students.append({"Index": index, "Name": name, "Start Time": time, "End Time": "In class"})
    html_students.append({"Index": index, "Name": name, "Start Time": time, "End Time": "In class", "Type": type, "Meeting": meeting})
    print(name, "logged in at", time)


def time_in_centre(index):
    # Current time
    now = datetime.now()
    time = now.strftime("%H:%M")

    for i in range(len(students)):
        # If the student with specific index is found:
        if students[i]["Index"] == index:
            # Return the amount of time the student was in the centre
            student = students[i]
            time_list = time.split(":")
            hours_in = int(time_list[0]) - int(student["Start Time"].split(":")[0])
            minutes_in = int(time_list[1]) - int(student["Start Time"].split(":")[1])
            return hours_in, minutes_in
    print("Student not found")


def record_absences(l):
    for i in range(STUDENT_COUNT - 1, 0, -1):
        absent = True
        for j in range(len(l)):
            if l[j]["Index"] == i:
                absent = False
        if absent:
            try:
                if get_student(i) is None:
                    continue
                name = str(sheet[get_student(i)][6].split("(")[0]) + " " + str(sheet[get_student(i)][7])
                l.insert(0, {"Index": i, "Name": name, "Start Time": "ABSENT", "End Time": "ABSENT"})
            except:
                print("Improper format detected in student database: row " + str(i + 1))


def save_day():
    # Sort Students by index
    save_list = students.copy()
    save_list.sort(key=operator.itemgetter('Index'))

    # Record absent students in front of students list
    record_absences(save_list)
    # Converts student dictionaries into lists, in order to export in xlsx file
    for i in range(len(save_list)):
        save_list[i] = list(save_list[i].values())
    for i in range(STUDENT_COUNT):
        if get_student(i) is None:
            continue
        if sheet[get_student(i)] is None:
            continue
        if sheet[get_student(i)][6] is None or sheet[get_student(i)][7] is None:
            continue
        try:
            name = sheet[get_student(i)][6].split("(")[0] + " " + sheet[get_student(i)][7]
        except IndexError:
            name = "Null"
        in_list = False
        for j in range(len(save_list)):
            if name in save_list[j]:
                in_list = True
        if not in_list:
            save_list.append([i, name, "ABSENT", "ABSENT"])

    # Adds headers for xlsx file
    save_list.insert(0, ["Index", "Name", "Start Time", "End Time"])
    data_handle.data_export("Student Logins.xlsx", datetime.today().strftime("%Y-%m-%d"), save_list)


# Finds a student with a specific index in html_students
def find_student(index):
    for i in range(len(html_students)):
        if html_students[i]["Index"] == index:
            return i
    return None


# Finds a student with a specific index in the datasheet
def get_student(index):
    for i in range(len(sheet)):
        try:
            if int(sheet[i][2]) == index:
                return i
        except:
            continue
    return None


# STARTS PROGRAM
if __name__ == '__main__':
    # Run end_day() when exiting program
    # atexit.register(save_day())
    # Run website
    app.run(host="0.0.0.0")
