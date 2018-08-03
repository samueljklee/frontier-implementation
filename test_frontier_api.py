from urlFrontier import Frontier
from app import *
import unittest
import requests
import time

frontierFunc = Frontier()

class TestUrlFrontierComponents(unittest.TestCase):
    def test_1_next_empty_frontendqueue(self):
        expected_output = {"error": "Front-End Queue & Back-End Queue & Priority Queue are empty"}
        expected_status = 400
        url = "http://localhost:5000/api/v1/next"
        req = requests.get(url)
        self.assertEqual(req.json(), expected_output)
        self.assertEqual(req.status_code, expected_status)

    def test_2_schedule_correct_input(self):
        expected_output = {"status": "URL: https://www.phonearena.com/news/Google-Chrome-Virtual-Reality_id107265 successfully added into frontier."}
        expected_status = 200
        url = "http://localhost:5000/api/v1/schedule"
        payload = {
                "url": "https://www.phonearena.com/news/Google-Chrome-Virtual-Reality_id107265", 
                "last_request_at": 1533202136,
                "last_request_time": 2, 
                "final_page": False, 
                "white_list": True}

        req = requests.post(url, json=payload)
        self.assertEqual(req.json(), expected_output)
        self.assertEqual(req.status_code, expected_status)

    def test_3_next_after_frontendqueue_input(self):
        expected_output = {"final_page": False,
                            "id": "49620f79e7fb47dc89ae7c2bc6e680f5",
                            "last_request_at": 1533202136,
                            "last_request_time": 2,
                            "url": "https://www.phonearena.com/news/Google-Chrome-Virtual-Reality_id107265",
                            "white_list": True}
        expected_status = 200
        time.sleep(1)
        url = "http://localhost:5000/api/v1/next"
        req = requests.get(url)
        self.assertEqual(req.json(), expected_output)
        self.assertEqual(req.status_code, expected_status)
    
    def test_4_schedule_wrong_input_format(self):
        expected_output = {"status": "Incorrect format."}
        expected_status = 400
        url = "http://localhost:5000/api/v1/schedule"
        payload = {
                "url": "https://www.phonearena.com/news/Google-Chrome-Virtual-Reality_id107265", 
                "last_request_at": "1533202136",
                "last_request_time": 2, 
                "final_page": False, 
                "white_list": True}

        req = requests.post(url, json=payload)
        self.assertEqual(req.json(), expected_output)
        self.assertEqual(req.status_code, expected_status)

        payload = {
                "url": "https://www.phonearena.com/news/Google-Chrome-Virtual-Reality_id107265", 
                "last_request_at": 1533202136,
                "last_request_time": 2, 
                "final_page": 2, 
                "white_list": True}

        req = requests.post(url, json=payload)
        self.assertEqual(req.json(), expected_output)
        self.assertEqual(req.status_code, expected_status)

        payload = {
                "url": 123456, 
                "last_request_at": 1533202136,
                "last_request_time": 2, 
                "final_page": False, 
                "white_list": True}

        req = requests.post(url, json=payload)
        self.assertEqual(req.json(), expected_output)
        self.assertEqual(req.status_code, expected_status)

    def test_5_commit_id_nonexist(self):
        expected_output = {"status": "Error Thread 49620f79e7fb47dc89ae7c2bc6e680f5 not active."}
        expected_status = 400
        url = "http://localhost:5000/api/v1/commit"
        payload = {"id": "49620f79e7fb47dc89ae7c2bc6e680f5"}

        req = requests.put(url, json=payload)
        self.assertEqual(req.json(), expected_output)
        self.assertEqual(req.status_code, expected_status)
        time.sleep(2)
    
    def test_6_commit_id_exist(self):
        expected_output = {"status": "Successfully commit message id 49620f79e7fb47dc89ae7c2bc6e680f5"}
        expected_status = 200
        url = "http://localhost:5000/api/v1/schedule"
        payload = {
                "url": "https://www.phonearena.com/news/Google-Chrome-Virtual-Reality_id107265", 
                "last_request_at": 1533202136,
                "last_request_time": 2, 
                "final_page": False, 
                "white_list": True}

        req = requests.post(url, json=payload)
        
        url = "http://localhost:5000/api/v1/next"
        req = requests.get(url)

        url = "http://localhost:5000/api/v1/commit"
        payload = {"id": "49620f79e7fb47dc89ae7c2bc6e680f5"}
        req = requests.put(url, json=payload)
        self.assertEqual(req.json(), expected_output)
        self.assertEqual(req.status_code, expected_status)

    def test_7_priority(self):
        estimated_output = {"final_page": True,
                            "id": "fd29801d0abfdc0f1ba19c84284f79be",
                            "last_request_at": 1532006053,
                            "last_request_time": 1,
                            "url": "https://spectrum.ieee.org",
                            "white_list": True}
        expected_status = 200
        url = "http://localhost:5000/api/v1/schedule"
        payload = {
                "url": "https://www.youtube.com/feed/histor", 
                "last_request_at": 1532006053,
                "last_request_time": 4, 
                "final_page": True, 
                "white_list": True}

        req = requests.post(url, json=payload)

        url = "http://localhost:5000/api/v1/schedule"
        payload = {
                "url": "https://spectrum.ieee.org", 
                "last_request_at": 1532006053,
                "last_request_time": 1, 
                "final_page": True, 
                "white_list": True}

        req = requests.post(url, json=payload)

        url = "http://localhost:5000/api/v1/schedule"
        payload = {
                "url": "https://www.phonearena.com", 
                "last_request_at": 1532006053,
                "last_request_time": 1, 
                "final_page": False, 
                "white_list": True}

        req = requests.post(url, json=payload)
        
        # We should receive youtube.com
        url = "http://localhost:5000/api/v1/next"
        req = requests.get(url)

        # 40% chance we'll receive spectrum.ieee.org
        url = "http://localhost:5000/api/v1/next"
        req = requests.get(url)
        print(" 40% chance to be correct: ")
        self.assertEqual(req.json(), estimated_output)
        self.assertEqual(req.status_code, expected_status)

    def tearDown(self):
        time.sleep(1)

if __name__ == "__main__":
    unittest.main(verbosity=2)