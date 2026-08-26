import enum


class UserRole(str, enum.Enum):
    COMPANY_ADMIN = "Company Admin"
    EMPLOYEE = "Employee"
    MANAGER = "Manager"
    ANALYST = "Analyst"
    VIEWER = "Viewer"
    SUPER_ADMIN = "Platform Super Admin"
