import React from 'react';
import ReactDOM from 'react-dom';
class BasicComponent extends React.Component {
  constructor(props) {
    super(props);
  }

  componentDidMount() {
    this.timerID = setInterval(
      () => this.tick(),
      1000
    );
  }

  componentWillUnmount() {
    clearInterval(this.timerID);
  }

  tick() {
  }

  render() {
    return (
      <div>
        <h1>Hello, world!</h1>
      </div>
    );
  }
}

export default BasicComponent;