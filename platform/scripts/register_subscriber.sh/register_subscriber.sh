#!/bin/bash

# Configuration
MONGO_SERVICE_NAME="mongo"
DB_NAME="open5gs"
DEFAULT_SST=1         # Default SST value
DEFAULT_SD="010203"   # Default SD value
DEFAULT_APN="internet" # Default APN

# Function to register a single UE
register_ue() {
    IMSI=$1
    KEY=$2
    OPC=$3

    echo "Registering UE: IMSI=$IMSI"

    # Add subscriber using open5gs-dbctl
    echo "Attempting to add subscriber $IMSI..."
    docker run -ti --rm --network ueransim_default -e DB_URI=mongodb://$MONGO_SERVICE_NAME/$DB_NAME gradiant/open5gs-dbctl:0.10.3 open5gs-dbctl add "$IMSI" "$KEY" "$OPC"
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to add subscriber $IMSI using open5gs-dbctl. Exit code: $?"
        # Try to get more info if possible
        docker run --rm --network ueransim_default mongo mongosh "mongodb://$MONGO_SERVICE_NAME/$DB_NAME" --eval "printjson(db.subscribers.findOne({imsi: '$IMSI'}))"
        return 1
    else
        echo "Subscriber $IMSI added successfully or already exists."
    fi

    # Update slice information using mongosh
    # This command first ensures a slice with the default SST exists, then sets its SD.
    # If no slice array exists, it creates one.
    # If a slice with the SST exists, it updates it.
    # If no slice with the SST exists, it adds a new slice object.
    echo "Attempting to update slice for $IMSI with SST=$DEFAULT_SST, SD=$DEFAULT_SD, APN=$DEFAULT_APN..."
    docker run --rm --network ueransim_default mongo mongosh "mongodb://$MONGO_SERVICE_NAME/$DB_NAME" --eval '''
    printjson(db.subscribers.updateOne(
        { "imsi": "'$IMSI'" },
        [
            {
                "$set": {
                    "slice": {
                        "$cond": {
                            if: { "$isArray": "$slice" },
                            then: {
                                "$let": {
                                    vars: {
                                        elemMatchIndex: {
                                            "$indexOfArray": [ "$slice.sst", '$DEFAULT_SST' ]
                                        }
                                    },
                                    in: {
                                        "$cond": {
                                            if: { "$ne": [ "$$elemMatchIndex", -1 ] },
                                            then: {
                                                "$concatArrays": [
                                                    { "$slice": [ "$slice", 0, "$$elemMatchIndex" ] },
                                                    [
                                                        {
                                                            "$mergeObjects": [
                                                                { "$arrayElemAt": [ "$slice", "$$elemMatchIndex" ] },
                                                                { "sst": '$DEFAULT_SST', "sd": "'$DEFAULT_SD'", "default_indicator": true, "session": [ { "name": "'$DEFAULT_APN'", "type": 2, "pcc_rule": [], "ambr": { "uplink": { "value": 1000, "unit": 3 }, "downlink": { "value": 1000, "unit": 3 } }, "qos": { "index": 9, "arp": { "priority_level": 8, "pre_emption_capability": 1, "pre_emption_vulnerability": 1 } } } ] }
                                                            ]
                                                        }
                                                    ],
                                                    { "$slice": [ "$slice", { "$add": [ "$$elemMatchIndex", 1 ] }, { "$size": "$slice" } ] }
                                                ]
                                            },
                                            else: {
                                                "$concatArrays": [
                                                    "$slice",
                                                    [ { "sst": '$DEFAULT_SST', "sd": "'$DEFAULT_SD'", "default_indicator": true, "session": [ { "name": "'$DEFAULT_APN'", "type": 2, "pcc_rule": [], "ambr": { "uplink": { "value": 1000, "unit": 3 }, "downlink": { "value": 1000, "unit": 3 } }, "qos": { "index": 9, "arp": { "priority_level": 8, "pre_emption_capability": 1, "pre_emption_vulnerability": 1 } } } ] } ]
                                                ]
                                            }
                                        }
                                    }
                                }
                            },
                            else: [ { "sst": '$DEFAULT_SST', "sd": "'$DEFAULT_SD'", "default_indicator": true, "session": [ { "name": "'$DEFAULT_APN'", "type": 2, "pcc_rule": [], "ambr": { "uplink": { "value": 1000, "unit": 3 }, "downlink": { "value": 1000, "unit": 3 } }, "qos": { "index": 9, "arp": { "priority_level": 8, "pre_emption_capability": 1, "pre_emption_vulnerability": 1 } } } ] } ]
                        }
                    }
                }
            }
        ]
    ))
    '''
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to update slice for $IMSI. Exit code: $?"
        return 1
    else
        echo "Slice update command executed for $IMSI."
    fi

    # Verify the subscriber document
    echo "Verifying subscriber $IMSI in database:"
    docker run --rm --network ueransim_default mongo mongosh "mongodb://$MONGO_SERVICE_NAME/$DB_NAME" --eval "printjson(db.subscribers.findOne({imsi: '$IMSI'}))"
    echo "-------------------------------------"
    return 0
}

# Remove the explicit database reset, as simple_ue_registration_test.sh handles cleanup
# echo "Attempting to reset database..."
# docker run -ti --rm --network ueransim_default -e DB_URI=mongodb://$MONGO_SERVICE_NAME/$DB_NAME gradiant/open5gs-dbctl:0.10.3 open5gs-dbctl reset
# if [ $? -ne 0 ]; then
#     echo "Database reset failed. Please check MongoDB and open5gs-dbctl tool. Exiting."
#     exit 1
# else
#     echo "Database reset successfully."
# fi

# Register multiple UEs
# IMSI format: MCC=999, MNC=70, MSIN (10 digits)
# UE1
register_ue "999700000000001" "fec86ba6eb707dec029d5258914c19c2" "465b5ce8b199b49faa5f0a2ee238a6bc"
# UE2
register_ue "999700000000002" "fec86ba6eb707dec029d5258914c19c3" "465b5ce8b199b49faa5f0a2ee238a6bd"
# UE3
register_ue "999700000000003" "fec86ba6eb707dec029d5258914c19c4" "465b5ce8b199b49faa5f0a2ee238a6be"

echo "Subscriber registration script finished."
