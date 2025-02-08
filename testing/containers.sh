#!/bin/bash

echo "Cleaning up existing containers..."
docker ps -a | grep 'endless-container-' | awk '{print $1}' | xargs -r docker rm -f
    
for i in {1..10}; do
    container_name="endless-container-$i"
    
    docker run -d \
        --name $container_name \
        alpine:latest \
        /bin/sh -c '
        while true; do
            # Get random message
            case $((RANDOM % 10)) in
                0) message="Processing data batch" ;;
                1) message="Updating cache" ;;
                2) message="Performing health check" ;;
                3) message="Analyzing metrics" ;;
                4) message="Running background task" ;;
                5) message="Cleaning temporary files" ;;
                6) message="Checking network connectivity" ;;
                7) message="Synchronizing data" ;;
                8) message="Executing scheduled job" ;;
                9) message="Monitoring system resources" ;;
            esac

            # Get random status
            case $((RANDOM % 5)) in
                0) status="SUCCESS" ;;
                1) status="WARNING" ;;
                2) status="INFO" ;;
                3) status="NOTICE" ;;
                4) status="DEBUG" ;;
            esac

            echo "[$(date "+%Y-%m-%d %H:%M:%S")] [$status] Container '$i': $message #$RANDOM"
            sleep $((RANDOM % 5 + 1))
        done'
    
    echo "Started container: $container_name"
done

echo "All containers are running."
