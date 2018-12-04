/***********************************************************************************************************************
*  Copyright (c) 2008-2018, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
*
*  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
*  following conditions are met:
*
*  (1) Redistributions of source code must retain the above copyright notice, this list of conditions and the following
*  disclaimer.
*
*  (2) Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
*  disclaimer in the documentation and/or other materials provided with the distribution.
*
*  (3) Neither the name of the copyright holder nor the names of any contributors may be used to endorse or promote products
*  derived from this software without specific prior written permission from the respective party.
*
*  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
*  INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
*  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE UNITED STATES GOVERNMENT, OR THE UNITED
*  STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
*  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
*  USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
*  STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
*  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
***********************************************************************************************************************/

import React from 'react';
import PropTypes from 'prop-types';
import IconButton from '@material-ui/core/IconButton';
import {FileUpload} from '@material-ui/icons';
import Grid from '@material-ui/core/Grid';
import TextField from '@material-ui/core/TextField';
import Button from '@material-ui/core/Button';
import { InputLabel, InputLabelProps } from '@material-ui/core/Input';
import LinearProgress from '@material-ui/core/LinearProgress';
import 'normalize.css/normalize.css';
import styles from './Upload.scss';
import {cyan500, red500, greenA200} from '@material-ui/core/colors';
import { graphql } from 'react-apollo';
import gql from 'graphql-tag';
import uuid from 'uuid/v1';

class FileInput extends React.Component {

  constructor(props) {
    super(props);
    this.fileInputRef = React.createRef();
    this.onChange = this.onChange.bind(this);
    this.onTextInputClick = this.onTextInputClick.bind(this);
    this.render = this.render.bind(this);
    this.state = {
      filename: ""
    };
  };

  static propTypes = {
    hint: PropTypes.string,
    onFileChange: PropTypes.func,
  };

  onChange(evt) {
    const file = evt.target.files[0];
    this.props.onFileChange(file);
    this.setState({filename: file.name});
  };

  onTextInputClick() {
    this.fileInputRef.current.click();
  };

  render() {
    return (
      <label className={styles.row}>
        <input type="file" className={styles.hidden} onChange={(evt) => { this.onChange(evt);}} ref={this.fileInputRef} />
        <TextField  fullWidth={true} label='Select OpenStudio or EnergyPlus File' onClick={() => {this.onTextInputClick}} value={this.state.filename}
          InputLabelProps={{
            shrink: this.state.filename != ""
          }}
        >
        </TextField>
      </label>
    )
  }
}

class Upload extends React.Component {

  constructor() {
    super();
    this.onModelFileChange = this.onModelFileChange.bind(this);
    this.onWeatherFileChange = this.onWeatherFileChange.bind(this);
    this.onClick = this.onClick.bind(this);
    this.uploadComplete = this.uploadComplete.bind(this);
    this.uploadProgress = this.uploadProgress.bind(this);

    this.state = {
      modelFile: null,
      weatherFile: null,
      uploadID: null,
      completed: 0
    };
  };

  static propTypes = {
    //className: PropTypes.string,
  };

  static contextTypes = {
    authenticated: PropTypes.bool,
    user: PropTypes.object
  };

  onModelFileChange(file) {
    this.setState({modelFile: file, completed: 0, uploadID: uuid()});
  }

  onWeatherFileChange(file) {
    this.setState({weatherFile: file, completed: 0});
  }

  uploadProgress(evt) {
    if (evt.lengthComputable) {
      var percentComplete = Math.round(evt.loaded * 100 / evt.total);
      if (percentComplete > 100) {
        this.setState({completed: 100});
      } else {
        this.setState({completed: percentComplete});
      }
    }
    else {
      console.log('percent: unable to compute');
    }
  }

  uploadComplete(evt) {
    /* This event is raised when the server send back a response */
    this.props.addJobProp(this.state.modelFile.name, this.state.uploadID);

    //var xhr = new XMLHttpRequest();

    //xhr.open('POST', '/job', true);
    //xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    //xhr.send(JSON.stringify({file: this.state.modelFile.name}));
  }

  uploadFailed(evt) {
    console.log("There was an error attempting to upload the file." + evt);
  }

  uploadCanceled(evt) {
    console.log("The upload has been canceled by the user or the browser dropped the connection.");
  }

  onClick() {
    if( this.state.modelFile ) {

      var formData = new FormData();
      formData.append('key', `uploads/${this.state.uploadID}/${this.state.modelFile.name}`);
      formData.append('acl', 'private');
      formData.append('policy', 'eyJleHBpcmF0aW9uIjoiMjA1MC0wMS0wMVQxMjowMDowMC4wMDBaIiwiY29uZGl0aW9ucyI6W3siYnVja2V0IjoiYWxmYWxmYSJ9LHsiYWNsIjoicHJpdmF0ZSJ9LHsieC1hbXotY3JlZGVudGlhbCI6IkFLSUFJSjNXUzNIWkRWUUc2NzZRLzIwNTAwMTAxL3VzLXdlc3QtMS9zMy9hd3M0X3JlcXVlc3QifSx7IngtYW16LWFsZ29yaXRobSI6IkFXUzQtSE1BQy1TSEEyNTYifSx7IngtYW16LWRhdGUiOiIyMDUwMDEwMVQwMDAwMDBaIn0sWyJzdGFydHMtd2l0aCIsIiRrZXkiLCJ1cGxvYWRzIl0sWyJjb250ZW50LWxlbmd0aC1yYW5nZSIsMCwxMDQ4NTc2MF1dfQ==');
      formData.append('x-amz-algorithm', 'AWS4-HMAC-SHA256');
      formData.append('x-amz-credential', 'AKIAIJ3WS3HZDVQG676Q/20500101/us-west-1/s3/aws4_request');
      formData.append('x-amz-date', '20500101T000000Z');
      formData.append('x-amz-signature', '57cf129426bbb95dab909a9696f208c5fb4d72d023a01ec0825e8c29faecf67c');
      formData.append('file', this.state.modelFile);

      var xhr = new XMLHttpRequest();

      xhr.upload.addEventListener("progress", this.uploadProgress, false);
      xhr.addEventListener("load", this.uploadComplete, false);
      xhr.addEventListener("error", this.uploadFailed, false);
      xhr.addEventListener("abort", this.uploadCanceled, false);

      //xhr.open('POST', 'https://alfalfa.s3.amazonaws.com', true);
      // TODO: Need to configure this on server side
      const posturl = 'http://' + window.location.hostname + ':9000/alfalfa';
      xhr.open('POST', posturl, true);

      xhr.send(formData);  // multipart/form-data
    } else {
      console.log('Select file to upload');
    }
  }

  modelFileHint() {
    if( this.state.modelFile ) {
      return this.state.modelFile.name;
    } else {
      return undefined;
    }
  }

  weatherFileHint() {
    if( this.state.weatherFile ) {
      return this.state.weatherFile.name;
    } else {
      return 'Select Weather File';
    }
  }

  render() {

    return (
      <div className={styles.root}>
        <LinearProgress variant="determinate" value={this.state.completed} />
        <div className={styles.center}>
          <Grid container>
            <Grid item xs={12}>
              <FileInput hint={this.modelFileHint()} onFileChange={this.onModelFileChange}/>
            </Grid>
            <Grid item xs>
              <Button fullWidth={true} variant="contained" color="primary" onClick={this.onClick}>Add Site</Button>
            </Grid>
            <Grid item xs>
              <Button fullWidth={true} variant="contained" color="primary" onClick={this.onClick}>Simulate</Button>
            </Grid>
          </Grid>
        </div>
      </div>
    );
  }
}

const addJobQL = gql`
  mutation addJobMutation($osmName: String!, $uploadID: String!) {
    addSite(osmName: $osmName, uploadID: $uploadID)
  }
`;

export default graphql(addJobQL, {
  props: ({ mutate }) => ({
    addJobProp: (osmName, uploadID) => mutate({ variables: { osmName, uploadID } }),
  }),
})(Upload);

