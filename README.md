Visenze Engineering Quiz - Frontier

By: Samuel Lee
===================================

How to run main program: 

        docker pull samueljklee/frontier-lee
        docker run -d -p 5000:5000 samueljklee/frontier-lee 
        (Runs app.py in background, feel free to use APIs with the right parameters (shown below))
        (http://localhost:5000/api/v1/schedule [POST])
        (http://localhost:5000/api/v1/next [GET])
        (http://localhost:5000/api/v1/commit [PUT])

How to run unit test: (RESTART frontier-lee before running EACH test files)

        docker restart [container id]
        docker exec [container id] /bin/sh -c "python3 test_frontier_api.py"

        docker restart [container id]
        docker exec [container id] /bin/sh -c "python3 test_frontier_functions.py"

To get container id:

        docker ps -a

To extract log file:

        docker cp [container id]:/frontier-app/frontier.log .

===================================

Summary
-----------------------------------
Frontier has been implemented based on the requirements from Visenze Engineering Quiz and based on the architecture according to the paper "[High-Performance Web Crawling](http://www.cs.cornell.edu/courses/cs685/2002fa/mercator.pdf)". 

The past few days have been challenging and fun. Learning to implement a data structure challenged me to design a well-structured code. However, after finishing up with the code, I noticed I could have done better on some part of the code which affected the ability to create a unit test for that portion. I did my best to fulfill the requirements and to match the architecture in the paper, I tried to have a few tweaks of my own too. I noticed a bug which I could not find the best solution with the remaining time, so, I made a few "soft fixes" for those bugs. Also, I have implemented a log file to ease debugging, it can be accesssed with the command shown above. 

===================================

Code
-----------------------------------
app.py:

        Flask app. Contains 3 API - schedule, next, commit

urlFrontier.py:

        prioritizer --> computes 5 priority level based on recent visit, load time, final page, and white list. Creates unique id for each messages. Add URL data into front_end_queue based on priority value. If Host-Queue Table is empty, initialize it with init_back_end_host_queue_table. 

        front_end_queue_selector --> Randomly chooses a queue with bias to high priority queues. Bias probability = [0.1 0.1 0.15 0.25 0.4].

        extract_hostname_path --> Extracts hostnames (HTTP, HTTPS, FTP, GOPHER).

        init_back_end_host_queue_table --> Initialize Host-Queue Table if it's empty.

        back_end_queue_router --> Obtain url from front_end_queue_selector. If hostname exists in Host-Queue Table, append url into table[hostname] and continue refilling back-end queue. If hostname doesn't exists, add it into table and add hostname into priority queue (heap) with the latest timestamp.

        update_priority_queue --> updates priority queue

        back_end_queue_selector --> selects the next message to resolve. If priority queue is empty, calls back_end_queue_router to add new host into queue. If length of *thread dict* = length of Host-Queue Table, this means all hostnames are currently in thread to await for Commit API (2 seconds), then program sleeps for 2 seconds. (Soft fix)(Should have a better way to do this.) Else, pop the top host from heap, return URL data of host, and calls start_commit_message_thread. 

        *thread dict* is a dictionary of information for creating and handling threads. thread[message id] = [ e, t ] e stands for event (to trigger each thread), t stands for threads.

        start_commit_message_thread --> starts threads through wait_commit_message to wait for Commit API. 

        wait_commit_message --> Program will wait for 2 seconds to receive Commit API. If received, pop the first url data from queue of hostname (FIFO). Else, add hostname back into priority queue with timestamp + 30 seconds. Both cases will call commit_ord_not.

        commit_or_not --> Checks for results of thread. If committed (pop url from hostname), check if queue in hostname is empty, if so, call back_end_queue_router to obtain current existing hostnames/ new hostname from front-end. If received new hostname, remove the hostname with empty queue. If not committed, add new hostname (to increase more variaty of hostnames to prevent hostnames from being called continuously).

        commit_message --> Commit API triggers this function to set event of thread dict.

test_frontier_api.py:

        Tests each API.

test_frontier_functions.py:

        Tests functions.

Schedule API input:
        {
        "url": "https://spectrum.ieee.org", 
        "last_request_at": 1532006053,
        "last_request_time": 1, 
        "final_page": false, 
        "white_list": false
        }

Schedule API output:
        {
        "status": "URL: https://spectrum.ieee.org successfully added into frontier."
        }

Next API output (no input):
        {
        "final_page": false,
        "id": "fd29801d0abfdc0f1ba19c84284f79be",
        "last_request_at": 1532006053,
        "last_request_time": 1,
        "url": "https://spectrum.ieee.org",
        "white_list": false
        }

Commit API input:
        {
        "id": "fd29801d0abfdc0f1ba19c84284f79be"
        }

Commit API output:
        {
        "status": "Successfully commit message id fd29801d0abfdc0f1ba19c84284f79be"
        }