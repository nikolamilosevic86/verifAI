import logo from './verifai-logo.png'
import './App.css';

function App() {
  return (
    <div className="App">
      <img className="App-logo" src={logo} alt="Logo"/>
      <div className="InputQuestion">
      <label className='QuestionLabel' for="question">Input your question in natural language</label><br/>
      <input id="question" name="question" className="QuestionClass" placeholder="e.g. What genes are promising targets for prostate cancer?"></input><button className='AskButton' role="button">Ask</button>
      </div>
    </div>
  );
}

export default App;
