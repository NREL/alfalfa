import Relay from "react-relay";

class AddJobMutation extends Relay.Mutation {
  getMutation() {
    return Relay.QL`
      mutation { addJob }
    `;
  }

  getVariables() {
    return {
      fileName: this.props.fileName
    };
  }

  getFatQuery() {
    return Relay.QL`
      fragment on AddJobPayload {
        result,
      }
    `;
    //return null;
  }

  getConfigs() {
    return [];
  }
}

export default AddJobMutation;
