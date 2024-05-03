import React, { Component } from 'react';
import logo from './verifai-logo.png';
import './App.css';


class MainScreen extends Component {
    constructor(props) {
        super(props);
        this.state = {
            modalOpen: false,
            value: "",
            temperature: 0,
            lex_parameter:0.5,
            sem_parameter:0.5,
            numDocuments: 10,
            startDate: "1940-01-01",
            endDate: "2030-01-01",
            search_type: "hybrid",
            submitted: false,
            loading: false,
            output: "" , // Holds HTML content safely
            output_verification: ""
        };
        
        this.postVerification = this.postVerification.bind(this)
        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
        this.setOutput = this.setOutput.bind(this);  // Binding setOutput for proper 'this' context
        this.setOutputVerification = this.setOutputVerification.bind(this)
        
        this.handleTemperatureChange = this.handleTemperatureChange.bind(this);
        this.handleNumDocumentsChange = this.handleNumDocumentsChange.bind(this);
        this.handleSearchTypeChange = this.handleSearchTypeChange.bind(this);
        this.handleStartDateChange = this.handleStartDateChange.bind(this);
        this.handleEndDateChange = this.handleEndDateChange.bind(this);

        this.handleLexParamChange = this.handleLexParamChange.bind(this);
        
        this.modalRef = React.createRef(); // Create a ref for the modal
        this.setWrapperRef = this.setWrapperRef.bind(this);             
        this.handleClickOutside = this.handleClickOutside.bind(this);

        
    }
    
    
    
    handleModalToggle = () => {
        this.setState(prevState => ({
          modalOpen: !prevState.modalOpen
        }));
      };

    
    handleLexParamChange = (event) => {
        const newValue = parseFloat(event.target.value);  // Ensure the value is treated as a number
        this.setState({
            lex_parameter: newValue,
            sem_parameter: 1 - newValue  // Automatically calculate the complementary value
        });
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
        this.setState({ output_verification: "" });
        
    }

    
    sendMessage = async () => {
        const { value,
              temperature, 
              numDocuments,
              startDate,
              endDate,
              search_type,
              lex_parameter,
              sem_parameter
             } = this.state;  // Using value from the state for the message
        const response = await fetch('http://3.74.47.54:5001/query/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: value,
                                   search_type: search_type,
                                   limit : numDocuments,
                                   filter_date_lte: endDate,
                                   filter_date_gte: startDate,
                                   temperature: temperature,
                                   lex_par:lex_parameter,
                                   semantic_par:sem_parameter,
                                })
        });
    
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        const baseUrl = "https://pubmed.ncbi.nlm.nih.gov/";
        const regex = /^\(\[\d+\]\)$/;
        const regex1 = /^\(\[\d+\]\)\.$/;
        const regex2 = /^\(\[\d+\]\)\;$/;
        const regex3 = /^\(\[\d+\]\)\,$/;
        const regex5 = /^\[\d+\]\.$/;
        const regex6 = /^\[\d+\]$/;
        const regex7 = /^\[\d+\]\,$/;
        const regex8 = /^\[\d+\]\;$/;
        const regex9 = /^\d+\)\.$/;
        const regex10 = /^\(\d+\)\.$/;
        const regex11 = /^\(\d+\)\$/;
        const regex12 = /^\(\[\d+\]\,$/;
        const regex13 = /^\[\d+\]\).$/;
        const processResult = async (result) => {
            if (result.done) {
                this.setState({loading:false});
                this.postVerification(this.state.output);
                return;
            }
            let token = decoder.decode(result.value, {stream: true});
            
            var no_space_token = token.trim()
            if (regex.test(no_space_token) || regex1.test(no_space_token) || regex2.test(no_space_token) || regex3.test(no_space_token)
                || regex5.test(no_space_token) || regex6.test(no_space_token) || regex7.test(no_space_token) || 
                regex8.test(no_space_token) || regex9.test(no_space_token) || regex10.test(no_space_token) ||
                regex11.test(no_space_token) || regex12.test(no_space_token) || regex13.test(no_space_token)) {
                no_space_token = no_space_token.replace(/[\[\]()\.,;]/g, '');
                var new_token = `<a href="${baseUrl + no_space_token}" target="_blank">${token}</a>`;
                token = new_token;
            }
            this.setOutput(token);
            await reader.read().then(processResult);
        };
    
        reader.read().then(processResult);
        
    }

    postVerification(completeText) {
        const baseUrl = "https://pubmed.ncbi.nlm.nih.gov/";
        fetch("http://3.74.47.54:5001/verification", {
            method: "POST",
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: completeText })
        })
        .then(response => {
            const readerVerification = response.body.getReader();
            const decoderVerification = new TextDecoder('utf-8');
    
            const processResultVerification = async (result) => {
                if (result.done) {
                    console.log("Streaming finished.");
                    return;
                }
                let claim_string = decoderVerification.decode(result.value, {stream: true});
                console.log(claim_string)
                var claim_dict = JSON.parse(claim_string);
                
                var ballHtml = (claim_dict.result === "SUPPORT") ? '  <span class="green-ball"></span>' :
                            (claim_dict.result === "NO REFERENCE") ? '  <span class="gray-ball"></span>' : ''
                            (claim_dict.result === "NO_EVIDENCE") ? '  <span class="yellow-ball"></span>' : ''
                            (claim_dict.result === "CONTRADICT") ? '  <span class="red-ball"></span>' : '';
                
                            console.log(claim_dict)

                console.log(typeof claim_dict)
                if (claim_dict["result"] === "NO REFERENCE") {
                    this.setOutputVerification("Claim:\n"+ claim_dict.claim + " <strong>" +claim_dict.result + "</strong>" +
                                                 ballHtml + "\n\n");
                } else {
                    // Otherwise, print claim, result, and pmid
                    var url_reference = `<a href="${baseUrl + claim_dict.pmid}" target="_blank">${claim_dict.pmid}</a>`;
                    
                    this.setOutputVerification("Claim for document " + url_reference + ':\n' + claim_dict.claim +  " " + 
                    "<strong>" + claim_dict.result + "</strong>" + ballHtml + "\n\n");
                    
                }
                
                // Read next portion of the stream
                return readerVerification.read().then(processResultVerification);
            };
    
            // Start reading the stream
            readerVerification.read().then(processResultVerification);
        })
        .catch(error => {
            console.error('Error during verification:', error);
        });
    }
    
    

    handleChange(event) {
        this.setState({ submitted: false });
        this.setState({ value: event.target.value });
    }

    handleSubmit(event) {
        
        event.preventDefault();
        this.setState({ submitted: true, loading:true });
        console.log("Loading", this.state.loading)
        this.clearOutput();
        this.sendMessage();

        this.setState({temperature: 0,
                      numDocuments: 10,
                      startDate: "1940-01-01",
                      endDate: "2030-01-01",
                      search_type: "hybrid",
                      lex_parameter:0.5,
                      sem_parameter:0.5,
                      });

    }

    

    setOutput(newOutput) {
        this.setState(prevState => ({
            output: prevState.output + newOutput
        }));
    }

    setOutputVerification(newOutput) {
        this.setState(prevState => ({
            output_verification: prevState.output_verification  + newOutput
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
                        <select value={this.state.search_type} onChange={this.handleSearchTypeChange}>
                            <option value="hybrid">Hybrid</option>
                            <option value="lexical">Lexical</option>
                            <option value="semantic">Semantic</option>
                        </select>
                    </label>

                     
                    {this.state.search_type === 'hybrid' && (
                    <div className="temperature-labels">
                        <label>
                            Lexical Weights:{this.state.lex_parameter.toFixed(3)}, Semantic Weights:{(1-this.state.lex_parameter).toFixed(3)}
                            <input 
                                type="range" 
                                min="0" 
                                max="1" 
                                value={this.state.lex_parameter}
                                step="0.01"
                                onChange={this.handleLexParamChange}
                            />
                            <button className="temperature-label start" onClick={() => this.setState({ lex_parameter: 0.3, sem_parameter: 0.7 })}>SEMANTIC</button>

                            <button className="temperature-label middle" onClick={() => this.setState({ lex_parameter: 0.5, sem_parameter: 0.5 })}>NEUTRAL</button>

                            <button className="temperature-label end" onClick={() => this.setState({ lex_parameter: 0.7, sem_parameter: 0.3 })}>LEXICAL</button>


                        </label>
                    </div>
                    )}
                    

    
                    
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


                    <form onSubmit={this.handleSubmit} className='QuestionClassForm'>
                    <input
                        id="question"
                        name="question"
                        className="QuestionClass"
                        placeholder="e.g. What genes are promising targets for prostate cancer?"
                        value={this.state.value}
                        onChange={this.handleChange}
                       
                    />
                    
                    <button className='AskButton' onClick={this.handleSubmit}>
                        Ask
                    </button>
                    </form>

                    </div>
                    

                    
                    {this.state.submitted && (
                    <div>
                        
                        <h2>{this.state.value} {this.state.loading && (<div className="spinner" />)}</h2>
                        
                       
                              
                       
                        
                        
                        <div className="output-section">     
                            <div className="output-tokens" dangerouslySetInnerHTML={{ __html: this.state.output }} />
                        </div>
                        
                        {!this.state.loading && (
                        <>
                            <h2>Fact Verification </h2>
                            <div className="output-verification">     
                            <div className="output-tokens" dangerouslySetInnerHTML={{ __html: this.state.output_verification }} />
                            </div>
                        </>
                        )}
                    </div>
                )}

                    

                  
                </div>
            </div>
        );
    }
}    

export default MainScreen;
