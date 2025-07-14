3GPP TS 38.331

5.5.4.4 Event A3 (Neighbour becomes offset better than SpCell)
The UE shall:
ETSI
3GPP TS 38.331 version 18.5.1 Release 18 261 ETSI TS 138 331 V18.5.1 (2025-04)
1> consider the entering condition for this event to be satisfied when condition A3-1, as specified below, is fulfilled;
1> consider the leaving condition for this event to be satisfied when condition A3-2, as specified below, is fulfilled;
1> use the SpCell for Mp, Ofp and Ocp.
NOTE 1: The cell(s) that triggers the event has reference signals indicated in the measObjectNR associated to this
event which may be different from the NR SpCell measObjectNR.
Inequality A3-1 (Entering condition)
Mn + Ofn + Ocn – Hys > Mp + Ofp + Ocp + Off
Inequality A3-2 (Leaving condition)
Mn + Ofn + Ocn + Hys < Mp + Ofp + Ocp + Off
The variables in the formula are defined as follows:
Mn is the measurement result of the neighbouring cell, not taking into account any offsets.
Ofn is the measurement object specific offset of the reference signal of the neighbour cell (i.e. offsetMO as defined
within measObjectNR corresponding to the frequency of the neighbour cell).
Ocn is the cell specific offset of the neighbour cell (i.e. cellIndividualOffset as defined within measObjectNR
corresponding to the frequency of the neighbour cell, or cellIndividualOffset as defined within reportConfigNR),
and set to zero if not configured for the neighbour cell.
Mp is the measurement result of the SpCell, not taking into account any offsets.
Ofp is the measurement object specific offset of the SpCell (i.e. offsetMO as defined within measObjectNR
corresponding to the SpCell).
Ocp is the cell specific offset of the SpCell (i.e. cellIndividualOffset as defined within measObjectNR corresponding
to the SpCell), and is set to zero if not configured for the SpCell.
Hys is the hysteresis parameter for this event (i.e. hysteresis as defined within reportConfigNR for this event).
Off is the offset parameter for this event (i.e. a3-Offset as defined within reportConfigNR for this event).
Mn, Mp are expressed in dBm in case of RSRP, or in dB in case of RSRQ and RS-SINR.
Ofn, Ocn, Ofp, Ocp, Hys, Off are expressed in dB.
NOTE 2: The definition of Event A3 also applies to CondEvent A3.

5.5.4.5 Event A4 (Neighbour becomes better than threshold)
The UE shall:
1> consider the entering condition for this event to be satisfied when condition A4-1, as specified below, is fulfilled;
1> consider the leaving condition for this event to be satisfied when condition A4-2, as specified below, is fulfilled.
Inequality A4-1 (Entering condition)
Mn + Ofn + Ocn – Hys > Thresh
Inequality A4-2 (Leaving condition)
Mn + Ofn + Ocn + Hys < Thresh
The variables in the formula are defined as follows:
Mn is the measurement result of the neighbouring cell or the measurement result of serving PSCell (i.e., in case it is
configured as candidate PSCell for CondEvent A4 evaluation) for CHO with candidate SCG(s) case, not taking
into account any offsets.
Ofn is the measurement object specific offset of the neighbour cell (i.e. offsetMO as defined within measObjectNR
corresponding to the frequency of the neighbour cell).
Ocn is the cell specific offset of the neighbour cell (i.e. cellIndividualOffset as defined within measObjectNR
corresponding to the frequency of the neighbour cell, or cellIndividualOffset as defined within reportConfigNR),
and set to zero if not configured for the neighbour cell.
Hys is the hysteresis parameter for this event (i.e. hysteresis as defined within reportConfigNR for this event).
Thresh is the threshold parameter for this event (i.e. a4-Threshold as defined within reportConfigNR for this event).
Mn is expressed in dBm in case of RSRP, or in dB in case of RSRQ and RS-SINR.
Ofn, Ocn, Hys are expressed in dB.
Thresh is expressed in the same unit as Mn.
NOTE: The definition of Event A4 also applies to CondEvent A4.

5.5.4.6 Event A5 (SpCell becomes worse than threshold1 and neighbour becomes
better than threshold2)
The UE shall:
1> consider the entering condition for this event to be satisfied when both condition A5-1 and condition A5-2, as
specified below, are fulfilled;
1> consider the leaving condition for this event to be satisfied when condition A5-3 or condition A5-4, i.e. at least
one of the two, as specified below, is fulfilled;
1> use the SpCell for Mp.
NOTE 1: The parameters of the reference signal(s) of the cell(s) that triggers the event are indicated in the
measObjectNR associated to the event which may be different from the measObjectNR of the NR SpCell.
Inequality A5-1 (Entering condition 1)
Mp + Hys < Thresh1
Inequality A5-2 (Entering condition 2)
Mn + Ofn + Ocn – Hys > Thresh2
Inequality A5-3 (Leaving condition 1)
Mp – Hys > Thresh1
Inequality A5-4 (Leaving condition 2)
Mn + Ofn + Ocn + Hys < Thresh2
The variables in the formula are defined as follows:
Mp is the measurement result of the NR SpCell, not taking into account any offsets.
Mn is the measurement result of the neighbouring cell, not taking into account any offsets.
Ofn is the measurement object specific offset of the neighbour cell (i.e. offsetMO as defined within measObjectNR
corresponding to the frequency of the neighbour cell).
Ocn is the cell specific offset of the neighbour cell (i.e. cellIndividualOffset as defined within measObjectNR
corresponding to the frequency of the neighbour cell, or cellIndividualOffset as defined within reportConfigNR),
and set to zero if not configured for the neighbour cell.
Hys is the hysteresis parameter for this event (i.e. hysteresis as defined within reportConfigNR for this event).
ETSI
3GPP TS 38.331 version 18.5.1 Release 18 263 ETSI TS 138 331 V18.5.1 (2025-04)
Thresh1 is the threshold parameter for this event (i.e. a5-Threshold1 as defined within reportConfigNR for this
event).
Thresh2 is the threshold parameter for this event (i.e. a5-Threshold2 as defined within reportConfigNR for this
event).
Mn, Mp are expressed in dBm in case of RSRP, or in dB in case of RSRQ and RS-SINR.
Ofn, Ocn, Hys are expressed in dB.
Thresh1is expressed in the same unit as Mp.
Thresh2 is expressed in the same unit as Mn.
NOTE 2: The definition of Event A5 also applies to CondEvent A5.

5.5.4.15 Event D1 (Distance between UE and referenceLocation1 is above threshold1
and distance between UE and referenceLocation2 is below threshold2)
The UE shall:
1> consider the entering condition for this event to be satisfied when both condition D1-1 and condition D1-2, as
specified below, are fulfilled;
1> consider the leaving condition for this event to be satisfied when condition D1-3 or condition D1-4, i.e. at least
one of the two, as specified below, are fulfilled;
Inequality D1-1 (Entering condition 1)
Ml1 – Hys > Thresh1
Inequality D1-2 (Entering condition 2)
Ml2 + Hys < Thresh2Inequality D1-3 (Leaving condition 1)
Ml1 + Hys < Thresh1
Inequality D1-4 (Leaving condition 2)
Ml2 – Hys > Thresh2
The variables in the formula are defined as follows:
Ml1 is the distance between UE and a reference location for this event (i.e. referenceLocation1 as defined within
reportConfigNR for this event), not taking into account any offsets.
Ml2 is the distance between UE and a reference location for this event (i.e. referenceLocation2 as defined within
reportConfigNR for this event), not taking into account any offsets.
Hys is the hysteresis parameter for this event (i.e. hysteresisLocation as defined within reportConfigNR for this
event).
Thresh1 is the threshold for this event defined as a distance, configured with parameter
distanceThreshFromReference1, from a reference location configured with parameter referenceLocation1 within
reportConfigNR for this event.
Thresh2 is the threshold for this event defined as a distance, configured with parameter
distanceThreshFromReference2, from a reference location configured with parameter referenceLocation2 within
reportConfigNR for this event.
Ml1 is expressed in meters.
Ml2 is expressed in the same unit as Ml1.
Hys is expressed in the same unit as Ml1.
Thresh1 is expressed in the same unit as Ml1.
Thresh2 is expressed in the same unit as Ml1.
NOTE: The definition of Event D1 also applies to CondEvent D1.

5.5.4.15a Event D2 (Distance between UE and the serving cell moving reference
location is above threshold1 and distance between UE and a moving
reference location is below threshold2)
The UE shall:
1> consider the entering condition for this event to be satisfied when both condition D2-1 and condition D2-2, as
specified below, are fulfilled;
1> consider the leaving condition for this event to be satisfied when condition D2-3 or condition D2-4, i.e. at least
one of the two, as specified below, are fulfilled;
Inequality D2-1 (Entering condition 1)
Ml1 – Hys > Thresh1
Inequality D2-2 (Entering condition 2)
Ml2 + Hys < Thresh2
Inequality D2-3 (Leaving condition 1)
Ml1 + Hys < Thresh1
Inequality D2-4 (Leaving condition 2)
Ml2 – Hys > Thresh2
The variables in the formula are defined as follows:
Ml1 is the distance between UE and a moving reference location for this event, not taking into account any offsets.
The moving reference location is determined based on movingReferenceLocation and the corresponding epoch
time and satellite ephemeris for the serving cell broadcast in SIB19.
Ml2 is the distance between UE and a moving reference location for this event, not taking into account any offsets.
The moving reference location is determined based on the parameter referenceLocation and the corresponding
epoch time and satellite ephemeris configured within the MeasObjectNR associated to this event.
Hys is the hysteresis parameter for this event (i.e. hysteresisLocation as defined within reportConfigNR for this
event).
Thresh1 is the threshold for this event defined as a distance, configured with parameter
distanceThreshFromReference1 in reportConfigNR for this event, from a moving reference location determined
based on the parameter movingReferenceLocation and the corresponding epoch time and satellite ephemeris for
the serving cell broadcast in SIB19.
Thresh2 is the threshold for this event defined as a distance, configured with parameter
distanceThreshFromReference2 in reportConfigNR for this event, from a moving reference location determined
based on the parameter referenceLocation and the corresponding epoch time and satellite ephemeris configured
within the MeasObjectNR associated to this event.
Ml1 is expressed in meters.
Ml2 is expressed in the same unit as Ml1.
Hys is expressed in the same unit as Ml1.
Thresh1 is expressed in the same unit as Ml1.
Thresh2 is expressed in the same unit as Ml1.
NOTE: The definition of Event D2 also applies to CondEvent D2.

5.5.4.16 CondEvent T1 (Time measured at UE is within a duration from threshold)
The UE shall:
1> consider the entering condition for this event to be satisfied when condition T1-1, as specified below, is fulfilled;
1> consider the leaving condition for this event to be satisfied when condition T1-2, as specified below, is fulfilled;
Inequality T1-1 (Entering condition)
Mt > Thresh1
Inequality T1-2 (Leaving condition)
Mt > Thresh1 + Duration
The variables in the formula are defined as follows:
Mt is the time measured at UE.
Thresh1 is the threshold parameter for this event (i.e. t1-Threshold as defined within reportConfigNR for this
event).
Duration is the duration parameter for this event (i.e. duration as defined within reportConfigNR for this event).
Mt is expressed in ms.
Thresh1 is expressed in the same unit as Mt.
Duration is expressed in the same unit as Mt.
