import React, { Component } from 'react';
import NumericInput from 'react-numeric-input';
import logo from './verifai-logo.png';
import './App.css';


class MainScreen extends Component {
    constructor(props) {
        super(props);
        this.state = {
            modalOpen: false,
            value: "",
            temperature: 0,
            numDocuments: 10,
            startDate: "1940-01-01",
            endDate: "2030-01-01",
            search_type: "hybrid",
            output: ""  // Holds HTML content safely
        };
        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
        this.setOutput = this.setOutput.bind(this);  // Binding setOutput for proper 'this' context
        this.handleTemperatureChange = this.handleTemperatureChange.bind(this);
        this.handleNumDocumentsChange = this.handleNumDocumentsChange.bind(this);
        this.handleSearchTypeChange = this.handleSearchTypeChange.bind(this);
        this.handleStartDateChange = this.handleStartDateChange.bind(this);
        this.handleEndDateChange = this.handleEndDateChange.bind(this);

        this.modalRef = React.createRef(); // Create a ref for the modal
        this.setWrapperRef = this.setWrapperRef.bind(this);             
        this.handleClickOutside = this.handleClickOutside.bind(this);
    }
    
    
    handleModalToggle = () => {
        this.setState(prevState => ({
          modalOpen: !prevState.modalOpen
        }));
      };

    handleStartDateChange = (event) => {
        this.setState({ startDate: event.target.value });
      };
    
      handleEndDateChange = (event) => {
        this.setState({ endDate: event.target.value });
      };

    handleSearchTypeChange(event) {
        this.setState({ search_type: event.target.value });
    }

    handleTemperatureChange(event) {
        this.setState({ temperature: event.target.value });
    }

    handleNumDocumentsChange = (event) => {
        const numDocuments = event.target.value;
        
        this.setState({numDocuments: numDocuments,});
      }

    
    clearOutput(){
        this.setState({ output: "" });
    }

    
    sendMessage = async () => {
        const { value,
              temperature, 
              numDocuments,
              startDate,
              endDate,
              search_type,
             } = this.state;  // Using value from the state for the message
        const response = await fetch('http://3.74.47.54:5001/query/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: value,
                                   search_type: search_type,
                                   limit :numDocuments,
                                   filter_date_lte: endDate,
                                   filter_date_gte: startDate,
                                   temperature: temperature
                                })
        });
    
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
    
        const processResult = async (result) => {
            if (result.done) return;
            let token = decoder.decode(result.value, {stream: true});
            this.setOutput(token);
            await reader.read().then(processResult);
        };
    
        reader.read().then(processResult);
    }

    handleChange(event) {
        this.setState({ value: event.target.value });
    }

    handleSubmit(event) {
        event.preventDefault();
        this.clearOutput();
        this.sendMessage();
    }

    

    setOutput(newOutput) {
        this.setState(prevState => ({
            output: prevState.output + newOutput
        }));
    }

    setWrapperRef(node) {
        this.wrapperRef = node;
      }
      
    handleClickOutside(event) {
    if (this.wrapperRef && !this.wrapperRef.contains(event.target)) {
        this.setState({ modalOpen: false });
        }
    }
    
    componentDidMount() {
        document.addEventListener('mousedown', this.handleClickOutside);
      }
      
    componentWillUnmount() {
    document.removeEventListener('mousedown', this.handleClickOutside);
    }

    render() {
        return (
            <div className="App">
                <img className="App-logo" src={logo} alt="Logo" />
                <div className="InputQuestion">
                <div className='tabbed'><label htmlFor="question">
               
                Input your question in natural language:</label><br/>
                </div>
                    <div className = "search-area">
                    
                    <button id="settings-btn" onClick={this.handleModalToggle} aria-label="Settings">&#9881;</button>
                    {this.state.modalOpen && (
                    <div className="ModalContent" ref={this.setWrapperRef}>
                    <h2>Search Configuration</h2>
                    <label>Type of Search: 
                        <select value={this.state.searchType} onChange={this.handleSearchTypeChange}>
                            <option value="hybrid">Hybrid</option>
                            <option value="lexical">Lexical</option>
                            <option value="semantic">Semantic</option>
                        </select>
                    </label>
                        
                    <label>Number of Documents:
                    <select
                        value={this.state.numDocuments}
                        onChange={this.handleNumDocumentsChange}
                        title="Please select the number of documents"
                    >
                        <option value="10">Normal - 10 documents</option>
                        <option value="5">Small - 5 documents</option>
                        <option value="15">Large - 15 documents</option>
                        <option value="20">Extra Large - 20 documents</option>
                    </select>
                    </label>
                    <div class="date-picker-group">
                    <label htmlFor="start">From:</label>
                    <input
                        type="date"
                        id="start"
                        name="trip-start"
                        value={this.state.startDate}
                        onChange={this.handleStartDateChange}
                        min="1940-01-01"
                        max={this.state.endDate}
                    />
                    </div>

                    <div class="date-picker-group">
                    <label htmlFor="end">To:</label>
                    <input
                        type="date"
                        id="end"
                        name="trip-end"
                        value={this.state.endDate}
                        onChange={this.handleEndDateChange}
                        min={this.state.startDate}
                        max="2030-01-01"
                    />
                    </div>
                    

                <div className="temperature-labels">
                    <label>Temperature: {this.state.temperature}:
                    <p>The higher the temperature, the less accurate answers will be.</p>
                <input
                    type="range"
                    value={this.state.temperature}
                    min="0"
                    max="1"
                    step="0.01"
                    onChange={this.handleTemperatureChange}
                />
                
                <button className="temperature-label start" onClick={() => this.setState({ temperature: '0' })}>PRECISE</button>

                <button className="temperature-label middle" onClick={() => this.setState({ temperature: '0.5' })}>NEUTRAL</button>

                <button className="temperature-label end" onClick={() => this.setState({ temperature: '1' })}>CREATIVE</button>
                </label>
            
                </div>
                </div>
                    )}



                    <input
                        id="question"
                        name="question"
                        className="QuestionClass"
                        placeholder="e.g. What genes are promising targets for prostate cancer?"
                        value={this.state.value}
                        onChange={this.handleChange}
                    />
                    <button className='AskButton' role="button" onClick={this.handleSubmit}>Ask</button>
                    </div>
                    

                    
                    


                                        
                    <div className="OutputTokens" dangerouslySetInnerHTML={{__html: this.state.output}} />
                </div>
            </div>
        );
    }
}    

export default MainScreen;
