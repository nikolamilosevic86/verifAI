import logo from './verifai-logo.png'
import './App.css';
import React, { Component } from 'react';

class MainScreen extends Component {
    constructor(props) {
        super(props);
        this.state = { value: "",value_nr:"" ,items:[]};
        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
        this.handleKeyDown = this.handleKeyDown.bind(this);
      }
      handleChange(event) { this.setState({ value: event.target.value }); }

    handleSubmit(event) {
        this.setState({ value_nr: event.target.value});
        const request = require('superagent');
        var searchterm = document.getElementById('question').value;
            var gpu_api = "http://127.0.0.1:5001"
            const req = request.post(gpu_api + '/search_index').set({Accept: 'application/json' });
            req.send({"query":searchterm});
            req.end((end,res)=>{
                if (res==undefined || end !== null){
                          if (end.status == 404){
                            alert("Request failed. Please refresh page and try again")
                          }else{
                         // window.location.href='https://linguist.auth.eu-central-1.amazoncognito.com/login?client_id=1opjprr5da5hmchq24ri8jnjhi&response_type=token&scope=aws.cognito.signin.user.admin+email+openid&redirect_uri=https://linguist.skgt.int.bayer.com/auth.html';
                          }
                        }
                        console.log(res.body);
                        var annotations = res.body;
                        this.setState({items:annotations});
                    });
                
    
        this.forceUpdate();
       // window.location = "/results?search_term=" + this.state.value + "";
       // event.preventDefault();
      }

      handleKeyDown(e) {
        if (e.key === 'Enter') {
          this.handleSubmit(e);
        }
      }

render() {
    var items = this.state.items;
  return (
   
    <div className="App">
      <img className="App-logo" src={logo} alt="Logo"/>
      <div className="InputQuestion">
      <label className='QuestionLabel' for="question">Input your question in natural language</label><br/>
      <input id="question" name="question" className="QuestionClass" placeholder="e.g. What genes are promising targets for prostate cancer?"
      value={this.state.value} onChange={this.handleChange}
      onKeyDown={this.handleKeyDown}></input>
      <button className='AskButton' role="button" onClick={this.handleSubmit}>Ask</button>
      <div className="SearchQuery">
          <b>Search query: </b>{this.state.value}
        </div>
      <div className='Pendulum'><img className='Pendulumgif' src="pendulum.gif"></img></div>
      <ul>
            {items.map(item => (
                
                <div className='result_item'>
                    <div className='res_title'>{item.title} -- <a href={"https://pubmed.ncbi.nlm.nih.gov/"+item.pmid} target='_blank'>PMID:{item.pmid}</a></div>
                </div>
            ))}
            </ul>
      </div>
    </div>
  );
}
}

export default MainScreen;
