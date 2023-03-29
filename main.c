/*******************************************************************************
 * Copyright (c) 2012, 2022 IBM Corp., Ian Craggs
 *
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Eclipse Public License v2.0
 * and Eclipse Distribution License v1.0 which accompany this distribution.
 *
 * The Eclipse Public License is available at
 *   https://www.eclipse.org/legal/epl-2.0/
 * and the Eclipse Distribution License is available at
 *   http://www.eclipse.org/org/documents/edl-v10.php.
 *
 * Contributors:
 *    Ian Craggs - initial contribution
 *******************************************************************************/

/*****
 * Adapted to present command injection and buffer overflow vulnerabilities via a malicious PUBLISH message.
 * - Added command line argument parsing for broker IP, port, MQTT topic
 * - Added the processmsg method that processes incoming PUBLISH messages and shows the vulnerabilities
 *****/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>
#include "MQTTClient.h"

#define ADDRESS     "localhost"
#define PORT        "8088"
#define CLIENTID    "client"
#define TOPIC       "foo"
#define QOS         0

volatile MQTTClient_deliveryToken deliveredtoken;

void processmsg(char *topicName, int topicLen, MQTTClient_message *message){
    // Only process messages for the configured topic
    if(strcmp(topicName, TOPIC) == 0){
        // Store the message with the remaining command in a limited char array
        char command[100];
        sprintf(command, "cd /tmp; wget -q http://%s/file", (char*)message->payload);
        // Execute the complete command
        system(command);
    }
}

void delivered(void *context, MQTTClient_deliveryToken dt)
{
    printf("Message with token value %d delivery confirmed\n", dt);
    deliveredtoken = dt;
}

int msgarrvd(void *context, char *topicName, int topicLen, MQTTClient_message *message)
{
    // printf("Received: [%s][%d] %s\n", topicName, message->payloadlen, (char*)message->payload);

    processmsg(topicName, topicLen, message);

    MQTTClient_freeMessage(&message);
    MQTTClient_free(topicName);
    return 1;
}

void connlost(void *context, char *cause)
{
    printf("\nConnection lost\n");
    printf("     cause: %s\n", cause);
}

int main(int argc, char* argv[]) {

    char *address = ADDRESS;
    char *port = PORT;
    char *topic = TOPIC;
    int qos = QOS;

    opterr = 0;
    int opt;
    while ((opt = getopt(argc, argv, "a:p:t:q:")) != -1){
        switch (opt) {
            case 'a':
                address = optarg;
                break;
            case 'p':
                port = optarg;
                break;
            case 't':
                topic = optarg;
                break;
            case 'q':
                qos = atoi(optarg);
                break;
            case '?':
                return 1;
            default:
                abort();
        }
    }

    u_long full_address_size = strlen(address) + strlen(port);
    char full_address[full_address_size];
    sprintf(full_address, "%s:%s", address, port);

    MQTTClient client;
    MQTTClient_connectOptions conn_opts = MQTTClient_connectOptions_initializer;
    int rc;

    if ((rc = MQTTClient_create(&client, full_address, CLIENTID,
                                MQTTCLIENT_PERSISTENCE_NONE, NULL)) != MQTTCLIENT_SUCCESS)
    {
        printf("Failed to create client, return code %d\n", rc);
        rc = EXIT_FAILURE;
        goto exit;
    }

    if ((rc = MQTTClient_setCallbacks(client, NULL, connlost, msgarrvd, delivered)) != MQTTCLIENT_SUCCESS)
    {
        printf("Failed to set callbacks, return code %d\n", rc);
        rc = EXIT_FAILURE;
        goto destroy_exit;
    }

    conn_opts.keepAliveInterval = 20;
    conn_opts.cleansession = 1;
    if ((rc = MQTTClient_connect(client, &conn_opts)) != MQTTCLIENT_SUCCESS)
    {
        printf("Failed to connect to %s, return code %d\n", full_address, rc);
        rc = EXIT_FAILURE;
        goto destroy_exit;
    }

    printf("Subscribing to topic %s\nfor client %s using QoS%d\n\n"
           "Press Q<Enter> to quit\n\n", topic, CLIENTID, qos);

    rc = MQTTClient_subscribe(client, TOPIC, QOS);

    int ch;
    do
    {
        ch = getchar();
    } while (ch!='Q' && ch != 'q');

    if ((rc = MQTTClient_unsubscribe(client, topic)) != MQTTCLIENT_SUCCESS)
    {
        printf("Failed to unsubscribe, return code %d\n", rc);
        rc = EXIT_FAILURE;
    }

destroy_exit:
    MQTTClient_destroy(&client);
exit:
    return rc;
}