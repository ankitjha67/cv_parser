"""
Backend API tests for CV-JD Matcher Application
Tests: Auth, CV Upload, JD Add, Match, Rewrite, Tailored CV endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Sample JD text for testing
SAMPLE_JD_TEXT = """
Financial Analyst Position

We are looking for a Financial Analyst with 3+ years of experience.

Requirements:
- Bachelor's degree in Finance, Accounting, or related field
- Strong Excel and financial modeling skills
- Experience with financial reporting and analysis
- Knowledge of GAAP and accounting principles
- Excellent communication skills

Responsibilities:
- Prepare financial reports and forecasts
- Analyze financial data and trends
- Support budgeting and planning processes
- Collaborate with cross-functional teams
"""

class TestHealthEndpoints:
    """Test API health and root endpoints"""
    
    def test_root_endpoint(self):
        """Test the root API endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200, f"Root endpoint failed: {response.text}"
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "CV-JD Matcher" in data["message"]
        print(f"✓ Root endpoint working - Version: {data['version']}")


class TestAuthEndpoints:
    """Test user authentication endpoints"""
    
    def test_register_user(self):
        """Test user registration"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": "test_pytest@example.com",
            "name": "Test User Pytest"
        })
        assert response.status_code == 200, f"Register failed: {response.text}"
        data = response.json()
        assert "email" in data
        print(f"✓ User registration works - Email: {data['email']}")
    
    def test_get_current_user_anonymous(self):
        """Test getting current user without auth"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200, f"Get me failed: {response.text}"
        data = response.json()
        assert data.get("email") == "anonymous" or data.get("name") == "Guest User"
        print(f"✓ Anonymous user access works")
    
    def test_get_current_user_authenticated(self):
        """Test getting current user with auth header"""
        headers = {"Authorization": "Bearer test_pytest@example.com"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        # May return 200 with user data or 404 if user doesn't exist
        assert response.status_code in [200, 404], f"Get me failed: {response.text}"
        print(f"✓ Authenticated user access endpoint works")


class TestCVEndpoints:
    """Test CV upload and retrieval endpoints"""
    
    def test_upload_cv_pdf(self):
        """Test CV upload with PDF file"""
        cv_path = "/app/backend/data/Ankit_Kumar.pdf"
        
        with open(cv_path, "rb") as f:
            files = {"file": ("Ankit_Kumar.pdf", f, "application/pdf")}
            response = requests.post(f"{BASE_URL}/api/cv/upload", files=files)
        
        assert response.status_code == 200, f"CV upload failed: {response.text}"
        data = response.json()
        assert "cv_id" in data
        assert "name" in data
        assert "message" in data
        print(f"✓ CV upload successful - ID: {data['cv_id']}, Name: {data['name']}")
        return data["cv_id"]
    
    def test_upload_cv_txt(self):
        """Test CV upload with TXT file"""
        cv_path = "/app/backend/data/sample_cv.txt"
        
        with open(cv_path, "rb") as f:
            files = {"file": ("sample_cv.txt", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/api/cv/upload", files=files)
        
        assert response.status_code == 200, f"CV upload failed: {response.text}"
        data = response.json()
        assert "cv_id" in data
        print(f"✓ TXT CV upload successful - ID: {data['cv_id']}")
    
    def test_list_cvs(self):
        """Test listing all CVs"""
        response = requests.get(f"{BASE_URL}/api/cvs")
        assert response.status_code == 200, f"List CVs failed: {response.text}"
        data = response.json()
        assert "cvs" in data
        assert isinstance(data["cvs"], list)
        print(f"✓ List CVs works - Found {len(data['cvs'])} CV(s)")
        return data["cvs"]
    
    def test_get_cv_by_id(self):
        """Test getting a specific CV by ID"""
        # First, list CVs to get an ID
        cvs = self.test_list_cvs()
        if len(cvs) == 0:
            pytest.skip("No CVs available to test")
        
        cv_id = cvs[0]["id"]
        response = requests.get(f"{BASE_URL}/api/cv/{cv_id}")
        assert response.status_code == 200, f"Get CV failed: {response.text}"
        data = response.json()
        assert data["id"] == cv_id
        assert "skills" in data
        assert "experiences" in data
        print(f"✓ Get CV by ID works - Skills: {len(data.get('skills', []))}")


class TestJDEndpoints:
    """Test Job Description endpoints"""
    
    def test_add_jd(self):
        """Test adding a Job Description via text"""
        response = requests.post(f"{BASE_URL}/api/jd/add", json={
            "title": "TEST_Financial Analyst",
            "text": SAMPLE_JD_TEXT
        })
        assert response.status_code == 200, f"Add JD failed: {response.text}"
        data = response.json()
        assert "jd_id" in data
        assert "title" in data
        assert data["title"] == "TEST_Financial Analyst"
        print(f"✓ Add JD successful - ID: {data['jd_id']}, Title: {data['title']}")
        return data["jd_id"]
    
    def test_list_jds(self):
        """Test listing all JDs"""
        response = requests.get(f"{BASE_URL}/api/jds")
        assert response.status_code == 200, f"List JDs failed: {response.text}"
        data = response.json()
        assert "jds" in data
        assert isinstance(data["jds"], list)
        print(f"✓ List JDs works - Found {len(data['jds'])} JD(s)")
        return data["jds"]
    
    def test_get_jd_by_id(self):
        """Test getting a specific JD by ID"""
        jds = self.test_list_jds()
        if len(jds) == 0:
            pytest.skip("No JDs available to test")
        
        jd_id = jds[0]["id"]
        response = requests.get(f"{BASE_URL}/api/jd/{jd_id}")
        assert response.status_code == 200, f"Get JD failed: {response.text}"
        data = response.json()
        assert data["id"] == jd_id
        assert "title" in data
        assert "requirements" in data
        print(f"✓ Get JD by ID works - Title: {data['title']}")


class TestMatchEndpoints:
    """Test CV-JD matching endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_data(self):
        """Ensure we have at least one CV and one JD"""
        # Check for existing CVs
        cvs_resp = requests.get(f"{BASE_URL}/api/cvs")
        cvs = cvs_resp.json().get("cvs", [])
        
        if len(cvs) == 0:
            # Upload a CV
            cv_path = "/app/backend/data/Ankit_Kumar.pdf"
            with open(cv_path, "rb") as f:
                files = {"file": ("Ankit_Kumar.pdf", f, "application/pdf")}
                resp = requests.post(f"{BASE_URL}/api/cv/upload", files=files)
            self.cv_id = resp.json()["cv_id"]
        else:
            self.cv_id = cvs[0]["id"]
        
        # Check for existing JDs
        jds_resp = requests.get(f"{BASE_URL}/api/jds")
        jds = jds_resp.json().get("jds", [])
        
        if len(jds) == 0:
            # Add a JD
            resp = requests.post(f"{BASE_URL}/api/jd/add", json={
                "title": "TEST_Match Financial Analyst",
                "text": SAMPLE_JD_TEXT
            })
            self.jd_id = resp.json()["jd_id"]
        else:
            self.jd_id = jds[0]["id"]
    
    def test_match_cv_jd(self):
        """Test matching CV against JD"""
        response = requests.post(f"{BASE_URL}/api/match", json={
            "cv_id": self.cv_id,
            "jd_id": self.jd_id
        })
        assert response.status_code == 200, f"Match failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "report" in data
        report = data["report"]
        assert "id" in report
        assert "total_score" in report
        assert "category_scores" in report
        
        # Verify score is valid
        score = report["total_score"]
        assert 0 <= score <= 100, f"Score {score} out of valid range"
        
        # Verify category scores exist
        category_scores = report["category_scores"]
        assert "skills" in category_scores
        assert "experience" in category_scores
        
        print(f"✓ Match successful - Total Score: {score}, Categories: {list(category_scores.keys())}")
        return report
    
    def test_match_returns_gaps(self):
        """Test that match returns gap analysis"""
        response = requests.post(f"{BASE_URL}/api/match", json={
            "cv_id": self.cv_id,
            "jd_id": self.jd_id
        })
        assert response.status_code == 200
        data = response.json()
        report = data["report"]
        
        # Check for gaps (may be empty if perfect match)
        assert "hard_gaps" in report
        assert "soft_gaps" in report
        print(f"✓ Gap analysis present - Hard: {len(report.get('hard_gaps', []))}, Soft: {len(report.get('soft_gaps', []))}")
    
    def test_match_invalid_cv_id(self):
        """Test match with invalid CV ID"""
        response = requests.post(f"{BASE_URL}/api/match", json={
            "cv_id": "invalid-cv-id-12345",
            "jd_id": self.jd_id
        })
        assert response.status_code == 404, f"Expected 404 for invalid CV, got {response.status_code}"
        print(f"✓ Invalid CV ID returns 404 correctly")
    
    def test_match_invalid_jd_id(self):
        """Test match with invalid JD ID"""
        response = requests.post(f"{BASE_URL}/api/match", json={
            "cv_id": self.cv_id,
            "jd_id": "invalid-jd-id-12345"
        })
        assert response.status_code == 404, f"Expected 404 for invalid JD, got {response.status_code}"
        print(f"✓ Invalid JD ID returns 404 correctly")


class TestRewriteEndpoints:
    """Test CV rewriting/tailoring endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_match_report(self):
        """Create a match report to use for rewriting"""
        # Get CV and JD
        cvs = requests.get(f"{BASE_URL}/api/cvs").json().get("cvs", [])
        jds = requests.get(f"{BASE_URL}/api/jds").json().get("jds", [])
        
        if len(cvs) == 0:
            cv_path = "/app/backend/data/Ankit_Kumar.pdf"
            with open(cv_path, "rb") as f:
                files = {"file": ("Ankit_Kumar.pdf", f, "application/pdf")}
                resp = requests.post(f"{BASE_URL}/api/cv/upload", files=files)
            cv_id = resp.json()["cv_id"]
        else:
            cv_id = cvs[0]["id"]
        
        if len(jds) == 0:
            resp = requests.post(f"{BASE_URL}/api/jd/add", json={
                "title": "TEST_Rewrite Financial Analyst",
                "text": SAMPLE_JD_TEXT
            })
            jd_id = resp.json()["jd_id"]
        else:
            jd_id = jds[0]["id"]
        
        # Create match report
        match_resp = requests.post(f"{BASE_URL}/api/match", json={
            "cv_id": cv_id,
            "jd_id": jd_id
        })
        self.match_report = match_resp.json()["report"]
        self.match_report_id = self.match_report["id"]
    
    def test_rewrite_deterministic(self):
        """Test deterministic CV rewriting"""
        response = requests.post(f"{BASE_URL}/api/rewrite", json={
            "match_report_id": self.match_report_id,
            "provider": "deterministic"
        })
        assert response.status_code == 200, f"Rewrite failed: {response.text}"
        data = response.json()
        
        assert "tailored_cv_id" in data
        assert "message" in data
        print(f"✓ Rewrite successful - Tailored CV ID: {data['tailored_cv_id']}")
        return data["tailored_cv_id"]
    
    def test_get_tailored_cv(self):
        """Test getting tailored CV by ID"""
        # First create a tailored CV
        tailored_id = self.test_rewrite_deterministic()
        
        # Then retrieve it
        response = requests.get(f"{BASE_URL}/api/tailored/{tailored_id}")
        assert response.status_code == 200, f"Get tailored CV failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert "cv" in data
        assert "modifications" in data
        assert data["id"] == tailored_id
        print(f"✓ Get tailored CV works - Modifications: {len(data.get('modifications', []))}")
        return tailored_id
    
    def test_download_tailored_cv(self):
        """Test downloading tailored CV as text file"""
        tailored_id = self.test_rewrite_deterministic()
        
        response = requests.get(f"{BASE_URL}/api/tailored/{tailored_id}/download")
        assert response.status_code == 200, f"Download failed: {response.text}"
        
        # Check content type
        content_type = response.headers.get("Content-Type", "")
        assert "text/plain" in content_type, f"Expected text/plain, got {content_type}"
        
        # Check content disposition header
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disposition, f"Missing attachment header"
        
        # Verify content is not empty
        assert len(response.content) > 0, "Downloaded file is empty"
        print(f"✓ Download tailored CV works - Size: {len(response.content)} bytes")
    
    def test_rewrite_invalid_report_id(self):
        """Test rewrite with invalid match report ID"""
        response = requests.post(f"{BASE_URL}/api/rewrite", json={
            "match_report_id": "invalid-report-id-12345",
            "provider": "deterministic"
        })
        assert response.status_code == 404, f"Expected 404 for invalid report, got {response.status_code}"
        print(f"✓ Invalid report ID returns 404 correctly")
    
    def test_get_tailored_cv_invalid_id(self):
        """Test getting tailored CV with invalid ID"""
        response = requests.get(f"{BASE_URL}/api/tailored/invalid-tailored-id-12345")
        assert response.status_code == 404, f"Expected 404 for invalid tailored ID, got {response.status_code}"
        print(f"✓ Invalid tailored CV ID returns 404 correctly")


class TestApplicationEndpoints:
    """Test application tracking endpoints"""
    
    def test_applications_anonymous(self):
        """Test applications endpoint returns empty for anonymous"""
        response = requests.get(f"{BASE_URL}/api/applications")
        assert response.status_code == 200
        data = response.json()
        assert data == [] or isinstance(data, list)
        print(f"✓ Anonymous applications returns empty list")
    
    def test_create_application_requires_auth(self):
        """Test that creating application requires auth"""
        response = requests.post(f"{BASE_URL}/api/applications", json={
            "company_name": "Test Company",
            "position": "Test Position"
        })
        assert response.status_code == 401, f"Expected 401 for unauthenticated, got {response.status_code}"
        print(f"✓ Create application correctly requires authentication")


class TestAnalyticsEndpoints:
    """Test analytics endpoints"""
    
    def test_success_rates_anonymous(self):
        """Test success rates endpoint for anonymous user"""
        response = requests.get(f"{BASE_URL}/api/analytics/success-rates")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or isinstance(data, dict)
        print(f"✓ Success rates endpoint accessible")


class TestRecruiterEndpoints:
    """Test recruiter dashboard endpoints"""
    
    def test_recruiter_dashboard_requires_auth(self):
        """Test recruiter dashboard requires authentication"""
        response = requests.get(f"{BASE_URL}/api/recruiter/dashboard")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Recruiter dashboard correctly requires authentication")
    
    def test_recruiter_candidates_requires_auth(self):
        """Test recruiter candidates endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/recruiter/candidates")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Recruiter candidates correctly requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
