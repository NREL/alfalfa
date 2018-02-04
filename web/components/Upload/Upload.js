import React from 'react';
import PropTypes from 'prop-types';
import IconButton from 'material-ui/IconButton';
import {FileUpload} from 'material-ui-icons';
import Grid from 'material-ui/Grid';
import TextField from 'material-ui/TextField';
import Button from 'material-ui/Button';
import Input, { InputLabel, InputLabelProps } from 'material-ui/Input';
import { FormControl, FormHelperText } from 'material-ui/Form';
import {LinearProgress} from 'material-ui/Progress';
import 'normalize.css/normalize.css';
import styles from './Upload.scss';
import {cyan500, red500, greenA200} from 'material-ui/colors';
import { graphql } from 'react-apollo';
import gql from 'graphql-tag';
import uuid from 'uuid/v1';

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
  }

  render() {
    return (
      <label className={styles.row}>
        <input id="foo" className={styles.hidden} type="file" onChange={this.onChange}/>
        <TextField fullWidth={true} label='Select OpenStudio or EnergyPlus File' value={this.props.hint}
          value={this.props.hint}
          InputLabelProps={{
            shrink: this.props.hint
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
    //if( this.state.modelFile ) {
    //  return this.state.modelFile.name;
    //} else {
    //  return 'Select OpenStudio or EnergyPlus File';
    //}
    if( this.state.modelFile ) {
      return this.state.modelFile.name;
    } else {
      return null;
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
        <LinearProgress mode="determinate" value={this.state.completed} />
        <div className={styles.center}>
          <Grid container>
            <Grid item xs={12}>
              <FileInput hint={this.modelFileHint()} onFileChange={this.onModelFileChange}/>
            </Grid>
            <Grid item xs>
              <Button fullWidth={true} raised color="primary" onClick={this.onClick}>Add Site</Button>
            </Grid>
            <Grid item xs>
              <Button fullWidth={true} raised color="primary" onClick={this.onClick}>Simulate</Button>
            </Grid>
          </Grid>
        </div>
      </div>
    );
  }
}

const addJobQL = gql`
  mutation addJobMutation($osmName: String!, $uploadID: String!) {
    addJob(osmName: $osmName, uploadID: $uploadID)
  }
`;

export default graphql(addJobQL, {
  props: ({ mutate }) => ({
    addJobProp: (osmName, uploadID) => mutate({ variables: { osmName, uploadID } }),
  }),
})(Upload);

