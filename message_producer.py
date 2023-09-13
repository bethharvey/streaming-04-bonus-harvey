"""
    This program sends a message to a queue on the RabbitMQ server.
    Make tasks harder/longer-running by adding dots at the end of the message.

    Author: Beth Harvey
    Date: September 12, 2023

"""

import pika
import sys
import webbrowser
import csv
import time

# Configure logging
from util_logger import setup_logger

logger, logname = setup_logger(__file__)

SHOW_OFFER = False

def offer_rabbitmq_admin_site():
    """Offer to open the RabbitMQ Admin website"""
    ans = input("Would you like to monitor RabbitMQ queues? y or n ")
    logger.info("Offer to monitor RabbitMQ queues.")
    if ans.lower() == "y":
        webbrowser.open_new("http://localhost:15672/#/queues")
        print(f"Answer is {ans}.")


def send_message(host: str, first_queue_name: str, second_queue_name: str, input_file: str):
    """
    Creates and sends a message to the queue each execution.
    This process runs and finishes.

    Parameters:
        host (str): the host name or IP address of the RabbitMQ server
        queue_name (str): the name of the queue
        input_file (str): the name of the CSV file to be read in as messages
    """

    try:
        # create a blocking connection to the RabbitMQ server
        conn = pika.BlockingConnection(pika.ConnectionParameters(host))
        # use the connection to create a communication channel
        ch = conn.channel()
        # use the channel to declare two durable queues
        # a durable queue will survive a RabbitMQ server restart
        # and help ensure messages are processed in order
        # messages will not be deleted until the consumer acknowledges
        ch.queue_declare(queue=first_queue_name, durable=True)
        ch.queue_declare(queue=second_queue_name, durable=True)

        # read each row from ramen-ratings.csv and send country to first queue and stars to second queue
        with open(input_file, 'r') as file:
            reader = csv.reader(file)
            # skip header row
            header = next(reader)
            for row in reader:
                # separate row into variables by column
                review_num, brand, variety, style, country, stars, top_ten = row
                # define first and second messages
                first_message = str(country)
                second_message = stars
                # use the channel to publish first message to first queue
                # every message passes through an exchange
                ch.basic_publish(exchange="", routing_key=first_queue_name, body=first_message)
                # print a message to the console for the user
                logger.info(f" [x] Sent {first_message} to {first_queue_name}")
                # publish second message to second queue
                ch.basic_publish(exchange="", routing_key=second_queue_name, body=second_message)
                # print a message to the console for the user
                logger.info(f"[x] Sent {second_message} to {second_queue_name}")
                # wait 3 seconds before sending the next message to the queue
                time.sleep(3)

    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Error: Connection to RabbitMQ server failed: {e}")
        sys.exit(1)
    finally:
        # close the connection to the server
        conn.close()

# Standard Python idiom to indicate main program entry point
# This allows us to import this module and use its functions
# without executing the code below.
# If this is the program being run, then execute the code below
if __name__ == "__main__": 
    # determine if offer_rabbitmq_admin_site() should be run 
    if SHOW_OFFER == True:
        # ask the user if they'd like to open the RabbitMQ Admin site
        offer_rabbitmq_admin_site()
    # send the message to the queue
    send_message("localhost","country_queue","stars_queue","ramen-ratings.csv")