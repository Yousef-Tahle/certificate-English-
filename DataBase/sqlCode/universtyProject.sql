CREATE DATABASE EnglishCertDB;
GO

USE EnglishCertDB;
GO

-- جدول المستخدمين (تسجيل الدخول)
CREATE TABLE Users (
    UserID      INT PRIMARY KEY IDENTITY(1,1),
    Username    NVARCHAR(50)  NOT NULL UNIQUE,
    Password    NVARCHAR(100) NOT NULL,
    Role        NVARCHAR(10)  NOT NULL CHECK (Role IN ('Admin', 'Student')),
    CreatedAt   DATETIME      DEFAULT GETDATE()
);

-- جدول الطلاب
CREATE TABLE Students (
    StudentID   INT PRIMARY KEY IDENTITY(1,1),
    UserID      INT FOREIGN KEY REFERENCES Users(UserID),
    FullName    NVARCHAR(100) NOT NULL,
    Email       NVARCHAR(100),
    Phone       NVARCHAR(20),
    BirthDate   DATE,
    Address     NVARCHAR(200)
);

-- جدول الدورات
CREATE TABLE Courses (
    CourseID    INT PRIMARY KEY IDENTITY(1,1),
    CourseName  NVARCHAR(100) NOT NULL,
    Description NVARCHAR(300),
    Duration    INT, -- عدد الأيام
    Price       DECIMAL(10,2),
    StartDate   DATE,
    EndDate     DATE
);

-- جدول الامتحانات
CREATE TABLE Exams (
    ExamID      INT PRIMARY KEY IDENTITY(1,1),
    ExamName    NVARCHAR(100) NOT NULL,
    ExamDate    DATETIME      NOT NULL,
    Location    NVARCHAR(200),
    MaxStudents INT,
    Fee         DECIMAL(10,2)
);

-- جدول التسجيلات (طالب في دورة أو امتحان)
CREATE TABLE Registrations (
    RegID       INT PRIMARY KEY IDENTITY(1,1),
    StudentID   INT FOREIGN KEY REFERENCES Students(StudentID),
    CourseID    INT FOREIGN KEY REFERENCES Courses(CourseID) NULL,
    ExamID      INT FOREIGN KEY REFERENCES Exams(ExamID) NULL,
    RegDate     DATETIME DEFAULT GETDATE(),
    Status      NVARCHAR(20) DEFAULT 'Pending' 
                CHECK (Status IN ('Pending','Confirmed','Cancelled'))
);

-- جدول النتائج
CREATE TABLE Results (
    ResultID    INT PRIMARY KEY IDENTITY(1,1),
    StudentID   INT FOREIGN KEY REFERENCES Students(StudentID),
    ExamID      INT FOREIGN KEY REFERENCES Exams(ExamID),
    Score       DECIMAL(5,2),
    Grade       NVARCHAR(10),
    IsPassed    BIT DEFAULT 0,
    ResultDate  DATE
);

-- جدول الشهادات
CREATE TABLE Certificates (
    CertID      INT PRIMARY KEY IDENTITY(1,1),
    StudentID   INT FOREIGN KEY REFERENCES Students(StudentID),
    ExamID      INT FOREIGN KEY REFERENCES Exams(ExamID),
    IssueDate   DATE DEFAULT GETDATE(),
    CertNumber  NVARCHAR(50) UNIQUE,
    Level       NVARCHAR(50)
);

-- إضافة Admin افتراضي
INSERT INTO Users (Username, Password, Role)
VALUES ('admin', '1234', 'Admin');