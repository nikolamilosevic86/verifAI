import React, { Component } from 'react';
import logo from './verifai-logo.png';
import { useNavigate } from 'react-router-dom';
import './App.css';
import { AuthContext} from './AuthContext';
import DOMPurify from 'dompurify';

function NavigateWrapper(props) {
    const navigate = useNavigate();

    return <MainScreen {...props} navigate={navigate} />;
}


class MainScreen extends Component {
   static contextType = AuthContext
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
        this.setOutput = this.setOutput.bind(this);  
        this.setOutputVerification = this.setOutputVerification.bind(this)
        
        this.handleTemperatureChange = this.handleTemperatureChange.bind(this);
        this.handleNumDocumentsChange = this.handleNumDocumentsChange.bind(this);
        this.handleSearchTypeChange = this.handleSearchTypeChange.bind(this);
        this.handleStartDateChange = this.handleStartDateChange.bind(this);
        this.handleEndDateChange = this.handleEndDateChange.bind(this);

        this.handleLexParamChange = this.handleLexParamChange.bind(this);
       
        this.handleLogout = this.handleLogout.bind(this)
        this.modalRef = React.createRef(); // Create a ref for the modal
        this.setWrapperRef = this.setWrapperRef.bind(this);             
        this.handleClickOutside = this.handleClickOutside.bind(this);

        
    }
    
    
    handleLogout = () => {
        this.context.logout();
        this.props.navigate('/login');
      };


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
                    this.setState({loading:false});
                    return;
                }
                
                let claim_string = decoderVerification.decode(result.value, {stream: true});
                
                
                var claim_dict = JSON.parse(claim_string); // receiving the result from backend
                //console.log("Result = ",claim_dict.result)
                
                if (Object.keys(claim_dict).length === 0) {
                    const ballHtml = ' <span class="gray-ball"></span>';
                    var color =  `<span class="tooltip" style="color: gray;">$1<span class="tooltiptext">The claim has <strong>NO REFERENCE</strong>${ballHtml}</span></span>`;
                    

                    const output = this.state.output;
                    var final_output = `<span class="tooltip" style="color: gray;">${output}<span class="tooltiptext">The claim has <strong>NO REFERENCE</strong>${ballHtml}</span></span>`;

                    
                    this.setState({ output: final_output });
                    this.setState({loading:false});
                    return
                }
                
                function tooltipToWrite(listResult) {
                    let text = "";
                    let color = "";
                    for (let [pmid,label] of Object.entries(listResult)) {
                        console.log("ENTRO NEL FOR")
                        if (color === "") {
                            color = (label === "SUPPORT") ? 'green' :
                                    (label === "NO REFERENCE") ? 'gray' :
                                    (label === "NO_EVIDENCE") ? 'yellow' :
                                    (label === "CONTRADICT") ? 'red' : '';
                        } else {
                            color = "blue"
                        }
                
                        let ballHtml = (label === "SUPPORT") ? '  <span class="green-ball"></span>' :
                                       (label === "NO REFERENCE") ? '  <span class="gray-ball"></span>' :
                                       (label === "NO_EVIDENCE") ? '  <span class="yellow-ball"></span>' :
                                       (label === "CONTRADICT") ? '  <span class="red-ball"></span>' : '';
                
                        let tooltipText = (label === "SUPPORT") ? `The claim for document <a href=${baseUrl + pmid}>${pmid}</a> is <strong>SUPPORT</strong>${ballHtml}` :
                                         (label === "NO REFERENCE") ? `The claim has <strong>NO REFERENCE</strong>${ballHtml}` :
                                         (label === "NO_EVIDENCE") ? `The claim for document <a href=${baseUrl + pmid}>${pmid}</a> has <strong>NO EVIDENCE</strong>${ballHtml}` :
                                         (label === "CONTRADICT") ? `The claim for document <a href=${baseUrl + pmid}>${pmid}</a> has <strong>CONTRADICTION</strong>${ballHtml}` : '';
                        
                        console.log(tooltipText)
                        text += "<br>" + tooltipText;
                        console.log("Text = ",text)
                    }
                    return { text: text, color: color };
                }
                

                const { text: text_toolpit, color: color_to_use } = tooltipToWrite(claim_dict.result);

                console.log("Text toolpit = ",text_toolpit)
                var color =  `<span class="tooltip" style="color: ${color_to_use};">$1<span class="tooltiptext">${text_toolpit}</span></span>` 
                            
                function escapeRegex(string) {
                    /* Replace just special char for the regex */
                    return string.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
                }

                    
                const output = this.state.output;
    
                const safeHTML = DOMPurify.sanitize(output);
                
                const tosearch = claim_dict.claim.trim();
                const escapedTosearch = escapeRegex(tosearch);
                let highlightedHTML;

                    
                const regexPattern = escapedTosearch.split('\\s+').join('\\s+(?:<[^>]*>\\s*)*');
                const claim_regex = new RegExp(`(${regexPattern})`, 'gi');

                highlightedHTML = safeHTML.replace(claim_regex, color);

                
                this.setState({ output: highlightedHTML });


                // ------------------------
                /*
                if (claim_dict["result"] === "NO REFERENCE") {
                    this.setOutputVerification("Claim:\n"+ claim_dict.claim + " <strong>" +claim_dict.result + "</strong>" +
                                                 ballHtml + "\n\n");
                } else {
                    // Otherwise, print claim, result, and pmid
                    var url_reference = `<a href="${baseUrl + claim_dict.pmid}" target="_blank">${claim_dict.pmid}</a>`;
                    
                    this.setOutputVerification("Claim for document " + url_reference + ':\n' + claim_dict.claim +  " " + 
                    "<strong>" + claim_dict.result + "</strong>" + ballHtml + "\n\n");
                    
                }
                */
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
            <AuthContext.Consumer>
                {({ user, logout }) => {
                    
                    if (!user) {
                        return (
                            <div className='App'>
                                <h1>Please log in to access this page.</h1>
                            </div>
                        );
                    }
                    
                    
                    
                    return (
                        <div className='App'>
                            <div className="router-reset">
                                <img className="App-logo" src={logo} alt="Logo" />
                                
                                <div className="InputQuestion">
                                    <div className='tabbed'>
                                        <label htmlFor="question">
                                            Input your question in natural language:
                                        </label>
                                        <br/>
                                    </div>
                                    <div className="search-area">
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
                                                            Lexical Weights: {this.state.lex_parameter.toFixed(3)}, Semantic Weights: {(1 - this.state.lex_parameter).toFixed(3)}
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
                                                <div className="date-picker-group">
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
                                                <div className="date-picker-group">
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
                                        <button className='LogoutButton' onClick={this.handleLogout}>Logout</button>
                                    </form>
                                </div>
                                <br></br>
                                {this.state.submitted && (
                                    <div>
                                        <h2>{this.state.value} {this.state.loading && (<div className="spinner" />)}</h2>
                                        <div className="output-section">     
                                            <div className="output-tokens" dangerouslySetInnerHTML={{ __html: this.state.output }} />
                                        </div>
                                       
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                );
            }}
        </AuthContext.Consumer>
    );
}
}

export default NavigateWrapper;
//export default MainScreen;