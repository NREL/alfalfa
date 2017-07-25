import React, { PropTypes } from 'react';
import IconButton from 'material-ui/IconButton';
import FileUpload from 'material-ui/svg-icons/file/file-upload';
import TextField from 'material-ui/TextField';
import FlatButton from 'material-ui/FlatButton';
import RaisedButton from 'material-ui/RaisedButton';
import 'normalize.css/normalize.css';
import styles from './Upload.scss';
import Paper from 'material-ui/Paper';
import {cyan500, red500, greenA200} from 'material-ui/styles/colors';
import { graphql } from 'react-apollo';
import gql from 'graphql-tag';

class FileInput extends React.Component {

  constructor() {
    super();
    this.onChange = this.onChange.bind(this);
  };

  static propTypes = {
    hint: PropTypes.string,
    onFileChange: PropTypes.func,
  };

  onChange(event) {
    const file = event.target.files[0];
    this.props.onFileChange(file);
    this.setState({label: file.name});
    
    console.log(file);
  }

  render() {
    return (
      <label className={styles.row}>
        <input id="foo" className={styles.hidden} type="file" onChange={this.onChange}/>
        <FileUpload style={{width: '38px', height: '38px'}} className={styles.icon} color={cyan500} />
        <div className={styles.fileinput} ref='label'>
          {this.props.hint}
        </div>
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

    this.state = {
      modelFile: null,
      weatherFile: null,
    };
  };

  static propTypes = {
    //className: PropTypes.string,
  };

  static contextTypes = {
    authenticated: React.PropTypes.bool,
    user: React.PropTypes.object
  };

  onModelFileChange(file) {
    this.setState({modelFile: file});
    console.log(file.name);
  }

  onWeatherFileChange(file) {
    this.setState({weatherFile: file});
    console.log(file.name);
  }

  uploadProgress(evt) {
    if (evt.lengthComputable) {
      var percentComplete = Math.round(evt.loaded * 100 / evt.total);
      console.log('percent: ' + percentComplete.toString() + '%');
    }
    else {
      console.log('percent: unable to compute');
    }
  }

  uploadComplete(evt) {
    /* This event is raised when the server send back a response */
    console.log("Done - " + evt.target.responseText );

    this.props.boom(this.state.modelFile.name);

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
      formData.append('key', 'uploads/' + this.state.modelFile.name);
      formData.append('acl', 'private');
      formData.append('policy', 'eyJleHBpcmF0aW9uIjoiMjA1MC0wMS0wMVQxMjowMDowMC4wMDBaIiwiY29uZGl0aW9ucyI6W3siYnVja2V0IjoiYWxmYWxmYSJ9LHsiYWNsIjoicHJpdmF0ZSJ9LHsieC1hbXotY3JlZGVudGlhbCI6IkFLSUFKUUxZUUo1SVNKVlBVN0lRLzIwNTAwMTAxL3VzLXdlc3QtMS9zMy9hd3M0X3JlcXVlc3QifSx7IngtYW16LWFsZ29yaXRobSI6IkFXUzQtSE1BQy1TSEEyNTYifSx7IngtYW16LWRhdGUiOiIyMDUwMDEwMVQwMDAwMDBaIn0sWyJzdGFydHMtd2l0aCIsIiRrZXkiLCJ1cGxvYWRzIl0sWyJjb250ZW50LWxlbmd0aC1yYW5nZSIsMCwxMDQ4NTc2MF1dfQ==');
      formData.append('x-amz-algorithm', 'AWS4-HMAC-SHA256');
      formData.append('x-amz-credential', 'AKIAJQLYQJ5ISJVPU7IQ/20500101/us-west-1/s3/aws4_request');
      formData.append('x-amz-date', '20500101T000000Z');
      formData.append('x-amz-signature', '642775cf022f034136fe8c23287e8a435fc11537f34f736249714f331a9f46c4');
      formData.append('file', this.state.modelFile);

      var xhr = new XMLHttpRequest();

      xhr.upload.addEventListener("progress", this.uploadProgress, false);
      xhr.addEventListener("load", this.uploadComplete, false);
      xhr.addEventListener("error", this.uploadFailed, false);
      xhr.addEventListener("abort", this.uploadCanceled, false);

      xhr.open('POST', 'https://alfalfa.s3.amazonaws.com', true);

      xhr.send(formData);  // multipart/form-data
    } else {
      console.log('Select file to upload');
    }
  }

  modelFileHint() {
    if( this.state.modelFile ) {
      return this.state.modelFile.name;
    } else {
      return 'Select Simulation File';
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
        <FileInput hint={this.modelFileHint()} onFileChange={this.onModelFileChange}/>
        <FileInput hint={this.weatherFileHint()} onFileChange={this.onWeatherFileChange}/>
        <RaisedButton label="Upload New Building Model!" primary={true} fullWidth={true} onClick={this.onClick}/>
      </div>
    );
  }
}

const boomy = gql`
  mutation boomish($fileName: String!) {
    addJob(fileName: $fileName)
  }
`;

export default graphql(boomy, {
  props: ({ mutate }) => ({
    boom: (fileName) => mutate({ variables: { fileName } }),
  }),
})(Upload);

