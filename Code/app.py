from flask import Flask, render_template, request, redirect, url_for, session
from database import get_connection

app = Flask(__name__)
app.secret_key = "englishcert2026"


# ========== الصفحة الرئيسية ==========
@app.route("/")
def index():
    return redirect(url_for("login"))


# ========== تسجيل الدخول ==========
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT UserID, Role FROM Users WHERE Username=? AND Password=?",
            (username, password),
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user.UserID
            session["role"] = user.Role
            if user.Role == "Admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("student_dashboard"))
        else:
            error = "اسم المستخدم أو كلمة المرور غلط"

    return render_template("login.html", error=error)


# ========== تسجيل الخروج ==========
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ========== لوحة Admin ==========
@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Students")
    students_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Courses")
    courses_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Exams")
    exams_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Certificates")
    certs_count = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin/dashboard.html",
        students_count=students_count,
        courses_count=courses_count,
        exams_count=exams_count,
        certs_count=certs_count,
    )


# ========== لوحة Student ==========
@app.route("/student/dashboard")
def student_dashboard():
    if "user_id" not in session or session["role"] != "Student":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    # جيب الـ StudentID
    cursor.execute(
        "SELECT StudentID FROM Students WHERE UserID=?", (session["user_id"],)
    )
    student = cursor.fetchone()

    courses_count = 0
    exams_count = 0
    certs_count = 0

    if student:
        cursor.execute(
            """
            SELECT COUNT(*) FROM Registrations
            WHERE StudentID=? AND CourseID IS NOT NULL
        """,
            (student.StudentID,),
        )
        courses_count = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*) FROM Registrations
            WHERE StudentID=? AND ExamID IS NOT NULL
        """,
            (student.StudentID,),
        )
        exams_count = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*) FROM Certificates
            WHERE StudentID=?
        """,
            (student.StudentID,),
        )
        certs_count = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "student/dashboard.html",
        courses_count=courses_count,
        exams_count=exams_count,
        certs_count=certs_count,
    )


# ========== إدارة الطلاب ==========
@app.route("/admin/students")
def admin_students():
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.StudentID, s.FullName, s.Email, s.Phone, s.BirthDate, u.Username
        FROM Students s
        JOIN Users u ON s.UserID = u.UserID
    """)
    students = cursor.fetchall()
    conn.close()

    return render_template("admin/students.html", students=students)


# ========== إضافة طالب ==========
@app.route("/admin/students/add", methods=["GET", "POST"])
def admin_add_student():
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        birthdate = request.form["birthdate"]
        address = request.form["address"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO Users (Username, Password, Role) VALUES (?, ?, 'Student')",
            (username, password),
        )
        cursor.execute("SELECT @@IDENTITY")
        user_id = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO Students (UserID, FullName, Email, Phone, BirthDate, Address)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (user_id, fullname, email, phone, birthdate, address),
        )

        conn.commit()
        conn.close()

        return redirect(url_for("admin_students"))

    return render_template("admin/add_student.html")


# ========== حذف طالب ==========
@app.route("/admin/students/delete/<int:student_id>")
def admin_delete_student(student_id):
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT UserID FROM Students WHERE StudentID=?", (student_id,))
    row = cursor.fetchone()

    if row:
        cursor.execute("DELETE FROM Students WHERE StudentID=?", (student_id,))
        cursor.execute("DELETE FROM Users WHERE UserID=?", (row.UserID,))
        conn.commit()

    conn.close()
    return redirect(url_for("admin_students"))


# ========== تعديل طالب ==========
@app.route("/admin/students/edit/<int:student_id>", methods=["GET", "POST"])
def admin_edit_student(student_id):
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        birthdate = request.form["birthdate"]
        address = request.form["address"]

        cursor.execute(
            """
            UPDATE Students
            SET FullName=?, Email=?, Phone=?, BirthDate=?, Address=?
            WHERE StudentID=?
        """,
            (fullname, email, phone, birthdate, address, student_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("admin_students"))

    # جيب بيانات الطالب الحالية
    cursor.execute(
        """
        SELECT s.*, u.Username FROM Students s
        JOIN Users u ON s.UserID = u.UserID
        WHERE s.StudentID = ?
    """,
        (student_id,),
    )
    student = cursor.fetchone()
    conn.close()

    return render_template("admin/edit_student.html", student=student)


# ========== إدارة الدورات ==========
@app.route("/admin/courses")
def admin_courses():
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Courses")
    courses = cursor.fetchall()
    conn.close()

    return render_template("admin/courses.html", courses=courses)


# ========== إضافة دورة ==========
@app.route("/admin/courses/add", methods=["GET", "POST"])
def admin_add_course():
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        duration = request.form["duration"]
        price = request.form["price"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Courses (CourseName, Description, Duration, Price, StartDate, EndDate)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (name, description, duration, price, start_date, end_date),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("admin_courses"))

    return render_template("admin/add_course.html")


# ========== حذف دورة ==========
@app.route("/admin/courses/delete/<int:course_id>")
def admin_delete_course(course_id):
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Courses WHERE CourseID=?", (course_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_courses"))


# ========== تعديل دورة ==========
@app.route("/admin/courses/edit/<int:course_id>", methods=["GET", "POST"])
def admin_edit_course(course_id):
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        duration = request.form["duration"]
        price = request.form["price"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]

        cursor.execute(
            """
            UPDATE Courses
            SET CourseName=?, Description=?, Duration=?,
                Price=?, StartDate=?, EndDate=?
            WHERE CourseID=?
        """,
            (name, description, duration, price, start_date, end_date, course_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("admin_courses"))

    cursor.execute("SELECT * FROM Courses WHERE CourseID=?", (course_id,))
    course = cursor.fetchone()
    conn.close()

    return render_template("admin/edit_course.html", course=course)


# ========== إدارة الامتحانات ==========
@app.route("/admin/exams")
def admin_exams():
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Exams")
    exams = cursor.fetchall()
    conn.close()

    return render_template("admin/exams.html", exams=exams)


# ========== إضافة امتحان ==========
@app.route("/admin/exams/add", methods=["GET", "POST"])
def admin_add_exam():
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        exam_date = request.form["exam_date"].replace("T", " ")
        location = request.form["location"]
        max_students = request.form["max_students"]
        fee = request.form["fee"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Exams (ExamName, ExamDate, Location, MaxStudents, Fee)
            VALUES (?, ?, ?, ?, ?)
        """,
            (name, exam_date, location, max_students, fee),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("admin_exams"))

    return render_template("admin/add_exam.html")


# ========== حذف امتحان ==========
@app.route("/admin/exams/delete/<int:exam_id>")
def admin_delete_exam(exam_id):
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Exams WHERE ExamID=?", (exam_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_exams"))


# ========== تعديل امتحان ==========
@app.route("/admin/exams/edit/<int:exam_id>", methods=["GET", "POST"])
def admin_edit_exam(exam_id):
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        exam_date = request.form["exam_date"].replace("T", " ")
        location = request.form["location"]
        max_students = request.form["max_students"]
        fee = request.form["fee"]

        cursor.execute(
            """
            UPDATE Exams
            SET ExamName=?, ExamDate=?, Location=?,
                MaxStudents=?, Fee=?
            WHERE ExamID=?
        """,
            (name, exam_date, location, max_students, fee, exam_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("admin_exams"))

    cursor.execute("SELECT * FROM Exams WHERE ExamID=?", (exam_id,))
    exam = cursor.fetchone()
    conn.close()

    return render_template("admin/edit_exam.html", exam=exam)


# ========== إدارة النتائج ==========
@app.route("/admin/results")
def admin_results():
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.ResultID, s.FullName, e.ExamName, 
               r.Score, r.Grade, r.IsPassed, r.ResultDate
        FROM Results r
        JOIN Students s ON r.StudentID = s.StudentID
        JOIN Exams e ON r.ExamID = e.ExamID
    """)
    results = cursor.fetchall()
    conn.close()

    return render_template("admin/results.html", results=results)


# ========== إضافة نتيجة ==========
@app.route("/admin/results/add", methods=["GET", "POST"])
def admin_add_result():
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        student_id  = request.form["student_id"]
        exam_id     = request.form["exam_id"]
        score       = request.form["score"]
        grade       = request.form["grade"]
        is_passed   = 1 if request.form.get("is_passed") else 0
        result_date = request.form["result_date"]

        cursor.execute("""
            INSERT INTO Results (StudentID, ExamID, Score, Grade, IsPassed, ResultDate)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, exam_id, score, grade, is_passed, result_date))
        conn.commit()
        conn.close()

        return redirect(url_for("admin_results"))

    # جيب الطلاب والامتحانات للقائمة المنسدلة
    cursor.execute("SELECT StudentID, FullName FROM Students")
    students = cursor.fetchall()

    cursor.execute("SELECT ExamID, ExamName FROM Exams")
    exams = cursor.fetchall()
    conn.close()

    return render_template("admin/add_result.html",
     students=students, exams=exams)


# ========== حذف نتيجة ==========
@app.route("/admin/results/delete/<int:result_id>")
def admin_delete_result(result_id):
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Results WHERE ResultID=?", (result_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_results"))


# ========== إدارة الشهادات ==========
@app.route("/admin/certificates")
def admin_certificates():
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.CertID, s.FullName, e.ExamName,
               c.IssueDate, c.CertNumber, c.Level
        FROM Certificates c
        JOIN Students s ON c.StudentID = s.StudentID
        JOIN Exams e ON c.ExamID = e.ExamID
    """)
    certificates = cursor.fetchall()
    conn.close()

    return render_template("admin/certificates.html", certificates=certificates)


# ========== إصدار شهادة ==========
@app.route("/admin/certificates/add", methods=["GET", "POST"])
def admin_add_certificate():
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        student_id = request.form["student_id"]
        exam_id = request.form["exam_id"]
        issue_date = request.form["issue_date"]
        cert_number = request.form["cert_number"]
        level = request.form["level"]

        cursor.execute(
            """
            INSERT INTO Certificates (StudentID, ExamID, IssueDate, CertNumber, Level)
            VALUES (?, ?, ?, ?, ?)
        """,
            (student_id, exam_id, issue_date, cert_number, level),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("admin_certificates"))

    # جيب الطلاب الناجحين والامتحانات
    cursor.execute("""
        SELECT DISTINCT s.StudentID, s.FullName
        FROM Results r
        JOIN Students s ON r.StudentID = s.StudentID
        WHERE r.IsPassed = 1
    """)
    students = cursor.fetchall()

    cursor.execute("SELECT ExamID, ExamName FROM Exams")
    exams = cursor.fetchall()
    conn.close()

    return render_template("admin/add_certificate.html", students=students, exams=exams)


# ========== حذف شهادة ==========
@app.route("/admin/certificates/delete/<int:cert_id>")
def admin_delete_certificate(cert_id):
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Certificates WHERE CertID=?", (cert_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_certificates"))


# ========== عرض التسجيلات ==========
@app.route("/admin/registrations")
def admin_registrations():
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.RegID, s.FullName,
               c.CourseName, e.ExamName,
               r.RegDate, r.Status
        FROM Registrations r
        JOIN Students s ON r.StudentID = s.StudentID
        LEFT JOIN Courses c ON r.CourseID = c.CourseID
        LEFT JOIN Exams e ON r.ExamID = e.ExamID
    """)
    registrations = cursor.fetchall()
    conn.close()

    return render_template("admin/registrations.html", registrations=registrations)


# ========== تغيير حالة التسجيل ==========
@app.route("/admin/registrations/status/<int:reg_id>/<status>")
def admin_update_registration(reg_id, status):
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Registrations SET Status=? WHERE RegID=?", (status, reg_id))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_registrations"))


# ========== نتائج الطالب ==========
@app.route("/student/results")
def student_results():
    if "user_id" not in session or session["role"] != "Student":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    # جيب الـ StudentID من الـ session
    cursor.execute(
        "SELECT StudentID FROM Students WHERE UserID=?", (session["user_id"],)
    )
    student = cursor.fetchone()

    results = []
    if student:
        cursor.execute(
            """
            SELECT e.ExamName, r.Score, r.Grade,
                   r.IsPassed, r.ResultDate
            FROM Results r
            JOIN Exams e ON r.ExamID = e.ExamID
            WHERE r.StudentID = ?
        """,
            (student.StudentID,),
        )
        results = cursor.fetchall()

    conn.close()
    return render_template("student/results.html", results=results)


# ========== شهادات الطالب ==========
@app.route("/student/certificates")
def student_certificates():
    if "user_id" not in session or session["role"] != "Student":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT StudentID FROM Students WHERE UserID=?", (session["user_id"],)
    )
    student = cursor.fetchone()

    certificates = []
    if student:
        cursor.execute(
            """
            SELECT e.ExamName, c.CertNumber,
                   c.Level, c.IssueDate
            FROM Certificates c
            JOIN Exams e ON c.ExamID = e.ExamID
            WHERE c.StudentID = ?
        """,
            (student.StudentID,),
        )
        certificates = cursor.fetchall()

    conn.close()
    return render_template("student/certificates.html", certificates=certificates)


# ========== تسجيل في دورة فقط ==========
@app.route("/student/register/course", methods=["GET", "POST"])
def student_register_course():
    if "user_id" not in session or session["role"] != "Student":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT StudentID FROM Students WHERE UserID=?", (session["user_id"],)
    )
    student = cursor.fetchone()

    if request.method == "POST" and student:
        course_id = request.form["course_id"]
        cursor.execute(
            """
            INSERT INTO Registrations (StudentID, CourseID)
            VALUES (?, ?)
        """,
            (student.StudentID, course_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("student_dashboard"))

    cursor.execute("SELECT CourseID, CourseName, Duration, Price FROM Courses")
    courses = cursor.fetchall()
    conn.close()

    return render_template("student/register_course.html", courses=courses)


# ========== تسجيل في امتحان فقط ==========
@app.route("/student/register/exam", methods=["GET", "POST"])
def student_register_exam():
    if "user_id" not in session or session["role"] != "Student":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT StudentID FROM Students WHERE UserID=?", (session["user_id"],)
    )
    student = cursor.fetchone()

    if request.method == "POST" and student:
        exam_id = request.form["exam_id"]
        cursor.execute(
            """
            INSERT INTO Registrations (StudentID, ExamID)
            VALUES (?, ?)
        """,
            (student.StudentID, exam_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("student_dashboard"))

    cursor.execute("SELECT ExamID, ExamName, ExamDate, Location, Fee FROM Exams")
    exams = cursor.fetchall()
    conn.close()

    return render_template("student/register_exam.html", exams=exams)


# ========== الملف الشخصي للطالب ==========
@app.route("/student/profile", methods=["GET", "POST"])
def student_profile():
    if "user_id" not in session or session["role"] != "Student":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        address = request.form["address"]

        cursor.execute(
            """
            UPDATE Students
            SET FullName=?, Email=?, Phone=?, Address=?
            WHERE UserID=?
        """,
            (fullname, email, phone, address, session["user_id"]),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("student_profile"))

    cursor.execute(
        """
        SELECT s.*, u.Username FROM Students s
        JOIN Users u ON s.UserID = u.UserID
        WHERE s.UserID=?
    """,
        (session["user_id"],),
    )
    student = cursor.fetchone()
    conn.close()

    return render_template("student/profile.html", student=student)


# ========== تعديل نتيجة ==========
@app.route("/admin/results/edit/<int:result_id>", methods=["GET", "POST"])
def admin_edit_result(result_id):
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        score = request.form["score"]
        grade = request.form["grade"]
        is_passed = 1 if request.form.get("is_passed") else 0
        result_date = request.form["result_date"]

        cursor.execute(
            """
            UPDATE Results
            SET Score=?, Grade=?, IsPassed=?, ResultDate=?
            WHERE ResultID=?
        """,
            (score, grade, is_passed, result_date, result_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("admin_results"))

    # جيب بيانات النتيجة الحالية
    cursor.execute(
        """
        SELECT r.*, s.FullName, e.ExamName
        FROM Results r
        JOIN Students s ON r.StudentID = s.StudentID
        JOIN Exams e ON r.ExamID = e.ExamID
        WHERE r.ResultID=?
    """,
        (result_id,),
    )
    result = cursor.fetchone()
    conn.close()

    return render_template("admin/edit_result.html", result=result)


# ========== تعديل شهادة ==========
@app.route("/admin/certificates/edit/<int:cert_id>", methods=["GET", "POST"])
def admin_edit_certificate(cert_id):
    if "user_id" not in session or session["role"] != "Admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        cert_number = request.form["cert_number"]
        level = request.form["level"]
        issue_date = request.form["issue_date"]

        cursor.execute(
            """
            UPDATE Certificates
            SET CertNumber=?, Level=?, IssueDate=?
            WHERE CertID=?
        """,
            (cert_number, level, issue_date, cert_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("admin_certificates"))

    cursor.execute(
        """
        SELECT c.*, s.FullName, e.ExamName
        FROM Certificates c
        JOIN Students s ON c.StudentID = s.StudentID
        JOIN Exams e ON c.ExamID = e.ExamID
        WHERE c.CertID=?
    """,
        (cert_id,),
    )
    cert = cursor.fetchone()
    conn.close()

    return render_template("admin/edit_certificate.html", cert=cert)


# ========== هاد دايماً آخر سطر ==========
if __name__ == "__main__":
    app.run(debug=True)
