import time, random, json, sys, logging, heapq, hashlib
from threading import Event, Thread, current_thread, Lock
from queue import Queue

class Frontier(object):
    number_of_front_end_queue = 5
    bias_probability = [0.1,0.1,0.15,0.25,0.4]

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.front_end_queue = [ [] for _ in range(self.number_of_front_end_queue) ]
        self.host_queue_mapping = dict()
        self.priority_queue = []
        self.threads = dict()
        self.mutex = Lock()

    def prioritizer(self, url, last_request_at, 
                last_request_time, final_page, white_list):
        """
            Computes priority value between 1 and k based on URL
            
            number_of_front_end_queue = 5 = k
            Variables affecting priority = last_request_at, last_request_time, final_page, white_list
            All variables have equal rates of 0.5 or -0.5
        
            Args:   url (string)
                    last_request_at (int)
                    last_request_time (int)
                    final_page (bool)
                    white_list (bool)  
            
            Return: Status code 1 (Successful), AssertionError (Errors)
        """
        priority_value = 0
        
        # Visited: > 1 hour : higher priority
        last_request_at_weight = abs(int(time.time()) - last_request_at)
        if (last_request_at_weight > 3600):
            priority_value += 0.5
        else:
            priority_value -= 0.5
        
        # Load time: <= 3 seconds : higher priority
        if last_request_time <= 3:
            priority_value += 0.5
        else:
            priority_value -= 0.5
        
        # Final page: True : higher priority
        if final_page:
            priority_value += 0.5
        else:
            priority_value -= 0.5

        # White list: True : higher priority
        if white_list:
            priority_value += 0.5
        else:
            priority_value -= 0.5
        
        # Priority value in range of 0 - 4
        priority_value += 2
        self.logger.debug(" URL {} Score: {}".format(url, priority_value))
        
        url_data = {
            "id": hashlib.md5((url+str(last_request_at)).encode("utf8")).hexdigest(),
            "url": url,
            "last_request_at": last_request_at,
            "last_request_time": last_request_time, 
            "final_page": final_page, 
            "white_list": white_list 
        }
        # Add url to queue based on priority value
        self.front_end_queue[int(priority_value)].append(url_data)
        self.logger.debug(" Front-End Queue {}".format(self.front_end_queue))

        # If Host-Queue Table is empty, add url
        if len(self.host_queue_mapping) == 0:
            self.init_back_end_host_queue_table()

        return url_data

    def front_end_queue_selector(self):
        """
            Randomly choose a queue with bias to high-priority queues

            Args: None

            Returns: First URL in the chosen queue (FIFO)
        """
        check_all_queue_empty = True
        self.logger.debug(" Front-end Queue Selector: {}".format(self.front_end_queue))
        
        for i in range(len(self.front_end_queue)):
            if len(self.front_end_queue[i]) == 0:
                check_all_queue_empty = True
            else:
                check_all_queue_empty = False
                break

        if check_all_queue_empty:
            self.logger.error("All Front-end Queue is empty.")
            raise AssertionError("All Front-end Queue is empty.")

        # Only choose a queue with item
        chosen_queue_front_end = random.choices(self.front_end_queue, self.bias_probability)[0]
        while len(chosen_queue_front_end) == 0:
            chosen_queue_front_end = random.choices(self.front_end_queue, self.bias_probability)[0]
        
        self.logger.info(" Front-end Queue selected url: {}".format(chosen_queue_front_end[0]))
        return chosen_queue_front_end.pop(0)
    
    def extract_hostname_path(self, url):
        """
            Extract hostname from HTTP, HTTPS, FTP, GOPHER

            Args: Url

            Return: Hostname, (protocol, path)
        """
        self.logger.debug(" Extracting hostname from {}".format(url))

        if "https" in url.lower():
            protocol = "https://"
        elif "http" in url.lower():
            protocol = "http://"
        elif "ftp" in url.lower():
            protocol = "ftp://"   
        elif "gopher" in url.lower():
            protocol = "gopher://"

        url = url.replace(protocol, "")
        
        # Path to subfiles
        if "/" in url:
            extraction = url.split("/")
            hostname = extraction.pop(0)
        else:
            hostname = url
        
        self.logger.debug(" Hostname: {} Url: {}".format(hostname, url))
        return hostname, url

    def init_back_end_host_queue_table(self):
        """
            Initialize Host-Queue table if it is empty

            Args: None

            Return: None (Return Host-Queue Table for debugging)
        """
        
        self.logger.debug(" Initializing Back-end Host-Queue Table.")
        url_data_from_front_end = self.front_end_queue_selector()
        hostname, url = self.extract_hostname_path(url_data_from_front_end['url'])
        self.host_queue_mapping[hostname] = [url_data_from_front_end]

        # Add host into priority queue
        self.update_priority_queue(hostname, 0)
        self.logger.debug(" Initialized Back-end Host-Queue Table {}".format(self.host_queue_mapping))

        return self.host_queue_mapping
        
    def back_end_queue_router(self):
        """
            Obtain URL from front_end_queue_selector.
            Create Host-Queue Table
            
            Args: None

            Return: -1 if front-end is empty (Return Host-Queue Table for debugging)
        """
        try:
            url_data_from_front_end = self.front_end_queue_selector()
        except AssertionError as exception_message:
            self.logger.warning(" {} Stop adding into Back-end Queue.".format(exception_message))
            #raise AssertionError(" {} Stop adding into Back-end Queue.".format(exception_message))
            return -1

        hostname, url = self.extract_hostname_path(url_data_from_front_end['url'])

        #try:
        # Add url into Back-end FIFO queue based on hostname.
        # Add hostname into priority_queue based on time of entry
        if hostname not in self.host_queue_mapping:
            self.host_queue_mapping[hostname] = [url_data_from_front_end]
            self.logger.debug(" New Hostname {}. Host-Queue: {}".format(hostname, self.host_queue_mapping[hostname]))
            # Add hostname into priority queue
            self.update_priority_queue(hostname, 0)
        else:
            self.host_queue_mapping[hostname].append(url_data_from_front_end)
            self.logger.debug(" Hostname exists {}. Host-Queue: {}".format(hostname, self.host_queue_mapping[hostname]))
            # Continue refill q
            self.logger.debug(" Continue refilling queue.")
            self.back_end_queue_router()
        """
        except:
            raise AssertionError("Fail to add hostname into Host-Queue Table.")
        """
        self.logger.debug(" Host-Queue Mapping: {}".format(self.host_queue_mapping))
        return self.host_queue_mapping

    def update_priority_queue(self, hostname, seconds):
        """
            Updates Priority Queue

            Args: None

            Return: None (Return priority queue for debugging)
        """
        timestamp = int(time.time()) + seconds
        heapq.heappush(self.priority_queue, (timestamp, hostname) )
        self.logger.debug(" Updating Priority Queue: Added ({},{})".format(timestamp, hostname))
        self.logger.debug(" New Priority Queue: {}".format(self.priority_queue))
        return self.priority_queue

    def back_end_queue_selector(self):
        """
            Selects the next message to resolve

            Args: None

            Return: URL (raise error if Front-End Queue & Back-End Queue & Priority Queue are empty)
        """
        if len(self.priority_queue) == 0:
            response = self.back_end_queue_router()
            if response == -1:
                if len(self.host_queue_mapping) != 0:
                    # Temporary solution for waiting for Commit API to be called. Waits 2 seconds in thread. 
                    # If there is thread running == hostname might be added back to queue if not committed.
                    while len(self.threads) == len(self.host_queue_mapping) :
                        time.sleep(2)
                if len(self.priority_queue) == 0:
                    raise AssertionError("Front-End Queue & Back-End Queue & Priority Queue are empty")

        # Extract top of the heap    
        smallest_timestamp_hostname = heapq.heappop(self.priority_queue)
        self.logger.debug(" Removed {} from priority queue: {}".format(smallest_timestamp_hostname, self.priority_queue))
        self.logger.debug(" Back_end Queue selected: {}".format(smallest_timestamp_hostname))
        self.logger.debug(" Back_end Queue hostname: {} url: {}".format(smallest_timestamp_hostname[1], self.host_queue_mapping[smallest_timestamp_hostname[1]][0]['url']))
        
        # Read data, remove after receiving acknowledgement 
        url_data_back_end = self.host_queue_mapping[smallest_timestamp_hostname[1]][0]
        
        ### Wait for commit API, if not commited, put back to queue
        self.start_commit_message_thread(smallest_timestamp_hostname[1], url_data_back_end)
        self.logger.debug(" Url Data Back End: {}".format(url_data_back_end))
        return url_data_back_end
    
    def commit_message(self, message_id):
        """
            Commit Message. Max 3 seconds wait.

            Args: None

            Return: Return if message is committed
        """
        print("Committing message {} -------------".format(message_id))
        if message_id in self.threads:
            self.logger.debug(" Thread {} is active. Setting thread ...".format(message_id))
            self.threads[message_id][0].set()
            return {'status': 'Successfully commit message id {}'.format(message_id)}
        else:
            self.logger.debug(" Thread {} not active.".format(message_id))
            raise AssertionError("Thread {} not active.".format(message_id))

    def start_commit_message_thread(self, hostname, url_data):
        """
            Start thread to wait for commit API
            If receive, pop data from host_queue_mapping
            If didn't receive in 2 seconds, push hostname back to priority queue

            Variables: 
                    self.threads[message_id] -> create threads based on message_id (for uniqueness)
                              "e"+message_id -> event for message_id
                              "t"+message_id -> thread for message_id
            
            Args hostname, url_data

            Return: None
        """
        message_id = url_data['id']
        if message_id not in self.threads:
            self.threads[message_id] = ["e"+message_id, "t"+message_id]
        
        self.threads[message_id][0] = Event()
        self.threads[message_id][1] = Thread(name=message_id,
                                                        target=self.wait_commit_message, 
                                                        args=(self.threads[message_id][0], 2, hostname))
        self.threads[message_id][1].start()

    def wait_commit_message(self, e, t, hostname):
        """
            Wait for Commit API
            After t=2 seconds, if ack is not received, put hostname back into queue with new timestamp + 30s
            Else, remove data from host_queue_mapping
            Calls commit_or_not to update Back-end Queue
            Remove message_id from threads

            Args: e (thread Event()), t (time to wait for Commit API), hostname

            Return: None
        """
        self.mutex.acquire()
        self.logger.debug('Thread {} waiting for commit.'.format(current_thread().name))
        event_is_set = e.wait(t)
        
        if not event_is_set:
            self.logger.debug("Thread {} fail to receive commit. Updating Priority Queue. Mutex Acquired".format(current_thread().name))
            
            self.update_priority_queue(hostname, 30)
            self.mutex.release()
            self.logger.debug("Thread {} added back to Priority Queue {}. Mutex Released".format(current_thread().name, self.priority_queue))
            # Remove itself from threads
            self.logger.debug(" Thread {} removed from threads.".format(current_thread().name))
            self.threads.pop(current_thread().name, None)
            self.commit_or_not(0, current_thread().name, hostname)
        else:
            self.host_queue_mapping[hostname].pop(0)
            self.mutex.release()
            self.logger.debug("Successfully committed. (FIFO) Removed first item of hostname {} from host-queue table {}".format(hostname, self.host_queue_mapping))
            # Remove itself from threads
            self.logger.debug(" Thread {} removed from threads.".format(current_thread().name))
            self.threads.pop(current_thread().name, None)
            self.commit_or_not(1, current_thread().name, hostname)

        

    def commit_or_not(self, thread_result, message_id, hostname):
        """
            Check if message is committed successsfully.
            thread_result -> 1: Successfully committed, -1: Fail to commit

            Successful Commit:
                        After extracting url from queue in host_queue_mapping 
                        Check of queue of hostname is empty
                        If empty, call back_end_queue_router to add to queue
                        Else, add hostname back to priority_queue with new timestamp for next item in queue 
            Fail Commit:
                        Add item into Back-end Queue until we get a new hostname
                        The goal is to have more vairant of URLs to choose from

            Args: thread_result, message_id, hostname

            Return: None
        """
        self.logger.debug("Thread {} result: {}".format(message_id, thread_result))

        if thread_result:
            if len(self.host_queue_mapping[hostname]) == 0:
                self.logger.debug(" Hostname {} Queue is empty. Refilling back-end Queue".format(hostname))
                response = self.back_end_queue_router()
                if response == -1:
                    while len(self.threads) == len(self.host_queue_mapping) :
                        time.sleep(2)
                    if len(self.priority_queue) == 0:
                        raise AssertionError("Front-End Queue & Back-End Queue & Priority Queue are empty")

                self.logger.debug(" New Host-Queue {}".format(self.host_queue_mapping))
                
                # Refilling will append current existing hostnames AND add new hostname
                # If added Hostname Y and Hostname X is still empty, remove it from table. 
                if len(self.host_queue_mapping[hostname]) == 0:
                    self.logger.debug(" New Host-Queue added. Hostname {} is empty. Removing from Host-Queue Table".format(hostname))
                    self.host_queue_mapping.pop(hostname, None)
                    return self.host_queue_mapping
            else:
                self.logger.error(" Hostname {} Queue is not empty. Adding Hostname back to Priority Queue".format(hostname))
                self.update_priority_queue(hostname, 0)
                return self.priority_queue
        else:
            # If fail to commit, add more into back_end_queue to have more variant of urls to choose
            #self.back_end_queue_router()
            
            response = self.back_end_queue_router()
            if response == -1:
                if len(self.priority_queue) == 0:
                    raise AssertionError(exception_message)
            return self.host_queue_mapping