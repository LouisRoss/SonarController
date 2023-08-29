import { useState, useEffect } from 'react';
import './App.css';
import SonarConfigField from './sonar-configfield';
import configuration from './configuration/configuration.json';
const baseBackendUrl = 'http://' + configuration.services.backend.host + ':' + configuration.services.backend.port;


const SonarConfigBoxNormal = ({onChangeFunc}) => {
    return (
        <div className="configurationbox">
          <div className="configurationgroup">
            Deployment
            <div className="configurationrow">
              <SonarConfigField fieldname="minutes" fieldTitle="Minutes after hour" initialValue="5" onChangeFunc={onChangeFunc}></SonarConfigField>
              <SonarConfigField fieldname="beamdatapoints" fieldTitle="Beam Data Points" initialValue="50" onChangeFunc={onChangeFunc}></SonarConfigField>
              <SonarConfigField fieldname="downwardsamplingtime" fieldTitle="Minutes for Downward Sampling" initialValue="0" onChangeFunc={onChangeFunc}></SonarConfigField>
            </div>
          </div>

          <div className="configurationgroup">
            Downward
            <div className="configurationrow">
              <SonarConfigField fieldname="downwardpencilbeamrange" fieldTitle="Pencil Beam Range (m)" initialValue="4" onChangeFunc={onChangeFunc}></SonarConfigField>
              <SonarConfigField fieldname="downwardfrequency" fieldTitle="Frequency (kHz)" initialValue="165" onChangeFunc={onChangeFunc}></SonarConfigField>
              <SonarConfigField fieldname="downwardpencilbeamlogf" fieldTitle="Pencil Beam logf (dB)" initialValue="1" onChangeFunc={onChangeFunc}></SonarConfigField>
              <SonarConfigField fieldname="downwardpencilbeamstartgain" fieldTitle="Pencil Beam Start Gain" initialValue="30" onChangeFunc={onChangeFunc}></SonarConfigField>
            </div>
            <div className="configurationrow">
              <SonarConfigField fieldname="downwardpencilbeamabsorption" fieldTitle="Pencil Beam Absorption" initialValue="60" onChangeFunc={onChangeFunc}></SonarConfigField>
              <SonarConfigField fieldname="downwardpencilbeampulselength" fieldTitle="Pencil Beam Pulse Length" initialValue="4" onChangeFunc={onChangeFunc}></SonarConfigField>
            </div>
          </div>

          <div className="configurationgroup">
            Scan
            <div className="configurationrow">
              <SonarConfigField fieldname="THREEDpencilbeamrange" fieldTitle="Pencil Beam Range (m)" initialValue="2" onChangeFunc={onChangeFunc}></SonarConfigField>
              <SonarConfigField fieldname="THREEDfrequency" fieldTitle="Frequency (kHz)" initialValue="165" onChangeFunc={onChangeFunc}></SonarConfigField>
              <SonarConfigField fieldname="THREEDpencilbeamlogf" fieldTitle="Pencil Beam logf Value" initialValue="1" onChangeFunc={onChangeFunc}></SonarConfigField>
              <SonarConfigField fieldname="THREEDpencilbeamstartgain" fieldTitle="Pencil Beam Start Gain" initialValue="30" onChangeFunc={onChangeFunc}></SonarConfigField>
            </div>
            <div className="configurationrow">
              <SonarConfigField fieldname="sampleperiod" fieldTitle="Seconds between Samples" initialValue="600" onChangeFunc={onChangeFunc}></SonarConfigField>
              <SonarConfigField fieldname="THREEDpencilbeamabsorption" fieldTitle="Pencil Beam Absorption" initialValue="60" onChangeFunc={onChangeFunc}></SonarConfigField>
              <SonarConfigField fieldname="THREEDpencilbeampulselength" fieldTitle="Pencil Beam Pulse Length (uSec)" initialValue="20" onChangeFunc={onChangeFunc}></SonarConfigField>
              <SonarConfigField fieldname="THREEDmodechoice" fieldTitle="3D Mode Choice" initialValue="1" onChangeFunc={onChangeFunc}></SonarConfigField>
            </div>
          </div>
        </div>
    )
}

export default SonarConfigBoxNormal;
