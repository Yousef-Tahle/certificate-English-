USE EnglishCertDB;
GO

CREATE TABLE Admins (
    AdminID  INT PRIMARY KEY IDENTITY(1,1),
    UserID   INT FOREIGN KEY REFERENCES Users(UserID),
    FullName NVARCHAR(100),
    Phone    NVARCHAR(20)
);

-- ربط الـ Admin الافتراضي اللي أضفناه سابقاً
INSERT INTO Admins (UserID, FullName, Phone)
VALUES (1, 'System Administrator', '0000000000');
