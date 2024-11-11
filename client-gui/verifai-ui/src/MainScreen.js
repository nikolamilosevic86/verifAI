import React, { Component,createRef,useContext, useState, createContext} from 'react';
import logo from './verifai-logo.png';
import ask from './new_ask.svg';
import new_settings from './new_settings.svg';
import share from './new_share.svg';
import link from './link.svg';
import facebook from './facebook.svg';
import linkedin from './linkedin.svg';
import twitter from './twitter.svg';
import checkmark from './checkmark.svg';
import logout_img from './new_logout.svg';
import { useNavigate } from 'react-router-dom';
import './MainScreen.css';
import {BACKEND} from './App.js'
import { AuthContext, useAuth} from './AuthContext';
import DOMPurify from 'dompurify';
import { DataContext } from './DataContext';
import { Helmet } from 'react-helmet';
import close from './close.svg';



function NavigateWrapper(props) {
    const navigate = useNavigate();
    const { setSharedData } = useContext(DataContext);

    return <MainScreen {...props} navigate={navigate} setSharedData={setSharedData} />
}


class MainScreen extends Component {
    

    
   static contextType = AuthContext
   static regex = /PUBMED:\d+/g;
    static regex_punct = /^\(PUBMED:\d+\)([\.\;\,])?$|^PUBMED:\d+\)$/g;
    static regex_square_brackets = /\(PUBMED:(\d+)\)/g;
    static regex_punct_2 = /^\(PUBMED:\d+\)([\.\;\,])?$|^PUBMED:\d+\)$/g;
    static regex_punct_3 = /^\(PUBMED:\d+\)[\.\;\,]?$/g;

    static file_regex = /FILE:\d+/g;
    static file_regex_punct = /^\(FILE:\d+\)([\.\;\,])?$|^FILE:\d+\)$/g;
    static file_regex_square_brackets = /\(FILE:(\d+)\)/g;
    static file_regex_punct_2 = /^\(FILE:\d+\)([\.\;\,])?$|^FILE:\d+\)$/g;
    static file_regex_punct_3 = /^\(FILE:\d+\)[\.\;\,]?$/g;
 
   
    constructor(props) {
        
        console.log("I am in the constructor");
        console.log(props);
        super(props);

        if (props.sessionData){
            const new_data = JSON.parse(props['sessionData']);
            this.state = new_data;
        } else {
        
            this.state = {
                
                modalOpen: false,
                sharingModalOpen: false,
                loginModalOpen: false,
                value: "",
                temperature: 0,
                lex_parameter:0.7,
                sem_parameter:0.3,
                numDocuments: 10,
                startDate: "1940-01-01",
                endDate: "2030-01-01",
                search_type: "hybrid",
                submitted: false,
                output: "" , // Holds HTML content safely
                output_verification: "",
                questions: [],
                stream: true,
                username: '',
                password: ''
            };  
        }
        
        this.componentRef = createRef();
        this.questionRef = createRef();
        this.usernameRef = createRef();
        this.captureStateAndHTML = this.captureStateAndHTML.bind(this)
        this.postVerification = this.postVerification.bind(this)
        this.saveSession = this.saveSession.bind(this);
        this.shareOnLinkedIn = this.shareOnLinkedIn.bind(this);
        this.shareOnFacebook = this.shareOnFacebook.bind(this);
        this.shareOnTwitter = this.shareOnTwitter.bind(this);
        this.downloadDocument = this.downloadDocument.bind(this);
        this.openSharingModal = this.openSharingModal.bind(this);
        this.copyLink = this.copyLink.bind(this);
        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
        this.setOutput = this.setOutput.bind(this);  
        this.setOutputVerification = this.setOutputVerification.bind(this)
        
        this.handleStreamChange = this.handleStreamChange.bind(this);
        this.handleTemperatureChange = this.handleTemperatureChange.bind(this);
        this.handleNumDocumentsChange = this.handleNumDocumentsChange.bind(this);
        this.handleSearchTypeChange = this.handleSearchTypeChange.bind(this);
        this.handleStartDateChange = this.handleStartDateChange.bind(this);
        this.handleEndDateChange = this.handleEndDateChange.bind(this);

        this.handleLexParamChange = this.handleLexParamChange.bind(this);
        this.handleLogout = this.handleLogout.bind(this);
        this.handleLogin = this.handleLogin.bind(this)
        this.handleUserCredential = this.handleUserCredential.bind(this);
        this.modalRef = React.createRef(); // Create a ref for the modal
        this.setWrapperRef = this.setWrapperRef.bind(this);             
        this.handleClickOutside = this.handleClickOutside.bind(this);
       
        this.handleTooltip = this.handleTooltip.bind(this);

        this.sharingModalRef = this.sharingModalRef.bind(this);
      

        this.handleCloseModal = this.handleCloseModal.bind(this);
        this.handleCloseSharingModal = this.hancleCloseSharingModal.bind(this);
        
        this.handleSaveQuestion = this.handleSaveQuestion.bind(this);
        this.handleLoginModalToggle = this.handleLoginModalToggle.bind(this);
        this.formLogin = this.formLogin.bind(this);
        this.formRegister = this.formRegister.bind(this);

        this.handleUsernameChange = this.handleUsernameChange.bind(this);
        this.handlePasswordChange = this.handlePasswordChange.bind(this);

        this.handleDocumentClick = this.handleDocumentClick.bind(this);

      


       


     

      
       
    }

   
    fetchData() {
        
        return {
            modalOpen: this.state.modalOpen,
            sharingModalOpen: this.state.sharingModalOpen,
            loginModalOpen: this.state.loginModalOpen,
            value: this.state.value,
            temperature: this.state.temperature,
            lex_parameter: this.state.lex_parameter,
            sem_parameter: this.state.sem_parameter,
            numDocuments: this.state.numDocuments,
            startDate: this.state.startDate,
            endDate: this.state.endDate,
            search_type: this.state.search_type,
            submitted: this.state.submitted,
            output: this.state.output,
            output_verification: this.state.output_verification
        };
    }
    
 

    handleStreamChange(event) {
        this.setState({ stream: event.target.value === "true" });
    }


    handleUserCredential = () => {
        this.props.navigate('/user_credential');
      };

    handleLogout = () => {
        this.context.logout();
        this.props.navigate('/login');
      };
    
      handleUsernameChange(event) {
        this.setState({ username: event.target.value });
      }
      
      handlePasswordChange(event) {
        this.setState({ password: event.target.value });
      }
      
      handleLogin = () => {
        const currentPath = window.location.pathname.substring(1);
       if(currentPath.includes('get_session'))
            this.props.navigate('/login?redirection=' + currentPath);
       else
         this.props.navigate('/login');
      };

      async loginFromModal(username, password)
      {
        const { login, setUser } = this.context;
        try{
        const response = await fetch(BACKEND + 'login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
                
            },
            body: JSON.stringify({ username: username, password: password })
        });

     

            if (response.ok) {
                const data = await response.json(); 
                localStorage.setItem("token",data.token);
                localStorage.setItem("username",username);
                //setUser({ token: data.token, username: username}); 
                const redirectionPath = window.location.pathname.substring(1)
                window.location.reload();
                
            } else if (response.status === 401) {
                alert('Invalid username or password');
            }
        } catch (error) {
            console.error('Login error:', error);
            alert('Login failed due to an unexpected error');
        }

      /*  if (this.context.user && this.context.user.token) {
            this.setState({ loginModalOpen: false });
            this.props.navigate('/main');
          }*/

        

      }

      async formLogin(event) {
        event.preventDefault();
        
    
        await this.loginFromModal(this.state.username, this.state.password);
    
       
      }
    
      



      formRegister = () => {
     
        this.props.navigate('/registration?redirection=' + window.location.pathname.substring(1));
        

      }

      


      handleSharingModalToggle = () => {
        this.setState(prevState => ({
            sharingModalOpen: !prevState.sharingModalOpen
        }));
    };

    handleModalToggle = () => {
        this.setState(prevState => ({
          modalOpen: !prevState.modalOpen
        }));
      };

      handleLoginModalToggle = () => {

        const redirectionPath = window.location.pathname.substring(1);
       
        this.setState(prevState => ({
          loginModalOpen: !prevState.loginModalOpen
        }), () => {
           
        });
       
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
       
        this.setState({numDocuments: numDocuments});
      }

    handleSaveQuestion = async (e) => {
      
        const username = this.usernameRef.current.textContent;
        const question = this.questionRef.current.value;
        
        
        try{
            
            const response = await fetch(BACKEND + 'main', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({username, question})
            });

            if(response.ok)
                console.log("Question saved successfully");
            else
               console.log("Error while saving question");
          

        }
        catch(error)
        {
            console.error("Error while saving question");
        }

    }

    
    clearOutput(){
        this.setState({ output: "" });
        this.setState({ output_verification: "" });
        
    }

    
    sendMessage = async (callback) => {
        const { value,
              temperature, 
              numDocuments,
              startDate,
              endDate,
              search_type,
              lex_parameter,
              sem_parameter
             } = this.state;  // Using value from the state for the message
        console.log("Num = ",this.state.numDocuments)
        
        const document_response = await fetch(BACKEND + 'query', {
            method: 'POST',
            headers: {
                'Authorization': "Bearer " + this.context.user.token, 
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: value,
                                   search_type: search_type,
                                   limit : numDocuments,
                                   filter_date_lte: endDate,
                                   filter_date_gte: startDate,
                                   lex_par:lex_parameter,
                                   semantic_par:sem_parameter,
                                })
                           

        }).catch(error => alert("An error occured, please try again."));

        
        const document_found = await document_response.json()
        
        console.log(document_found)
        this.setState(prevState => ({
            questions: prevState.questions.map((q, i) => (
                i === prevState.questions.length - 1 ? { ...q, document_found } : q
            )),
        }));

        console.log("Prima dello streaming ")
        console.log(this.state.questions[this.state.questions.length-1].document_found)
        if (callback) {
            callback();
        }
        
        const response = await fetch(BACKEND + 'stream_tokens', {
            method: 'POST',
            headers: {
                'Authorization': "Bearer " + this.context.user.token, 
                'Content-Type': 'application/json'
            },
            
            body: JSON.stringify({ query: value,
                                   temperature:temperature,
                                   document_found: document_found
                                })
        }).catch(error =>  alert("An error occurred, please try again later."));
    
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        const baseUrl = "https://pubmed.ncbi.nlm.nih.gov/";
        
        
        const processResult = async (result) => {
            if (result.done) {
                //this.setState({  });
                this.setState(prevState => ({
                    questions: prevState.questions.map((q, i) => (
                        i === prevState.questions.length - 1 ? { ...q, status: "fetching_verification", loading:true} : q
                    )),
                }));
                this.postVerification(this.state.questions[this.state.questions.length - 1].result);
                return;
            }
            let token = decoder.decode(result.value, {stream: true});
            
           
            var no_space_token = token.trim()
            console.log(no_space_token);
            
            const regex = /\(?PUBMED:(\d+)\)?/g;
            const file_regex = /\(?FILE:(\d+)\)?/g;
            

          
            if (regex.test(no_space_token)){
                
                const regex = /\(?PUBMED:(\d+)\)?/g; 
                var new_token = token;
             
                let match;
                while ((match = regex.exec(no_space_token)) !== null) {
                   
                    const number = match[1];
                    const matchedPart = match[0];
                   
                    const linkedPart = `<a href="${baseUrl + number}" target="_blank">${matchedPart}</a>`;
                    new_token = new_token.replace(matchedPart, linkedPart);
                }
            
                token = new_token;
              
            }
            const fileregex = /\[FILE:([\w\s\-./\\]+?\.(pdf|docx|pptx|txt|md))\]/i;

            // Replace the matched text with a clickable link
            const outputString = token.replace(fileregex, (match, filePath) => {
              // Convert the file path to a clickable link (replace backslashes with forward slashes if necessary)
              const formattedPath = filePath.replace(/\\/g, '/'); 
              return `<a href="#" data-download="true" target="_blank">${filePath}</a>`;
            });
            
            let newToken = outputString;

            // Set output synchronously
            this.setOutput(newToken);
            
            // Start the reader asynchronously and process the result concurrently
            reader.read().then(processResult); 
           
        };
    
        return reader.read().then(processResult);
        
    }

    captureStateAndHTML() {
        const currentState = this.state; // Capture the current state
    
        const htmlContent = this.componentRef.current ? this.componentRef.current.outerHTML : '';
                
        const getCircularReplacer = () => {
            const seen = new WeakSet();
            return (key, value) => {
                if (typeof value === "object" && value !== null) {
                    if (seen.has(value)) {
                        return;
                    }
                    seen.add(value);
                }
                return value;
            };
        };

        const stateString = JSON.stringify(currentState, getCircularReplacer());
        return { state: stateString, html: htmlContent };
    }

    saveSession() {
        
        const { state, _ } = this.captureStateAndHTML(); // Make sure you have implemented this method
       
        fetch(BACKEND + `save_session`, {
            method: "POST",
            headers: {
                'Authorization': "Bearer " + this.context.user.token, 
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ state: state })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Session saved with ID:', data.session_id);
            //this.props.navigate(`/get_session/${data.session_id}`);
           // window.open(`/get_session/${data.session_id}`, '_blank');
           const baseUrl = window.location.protocol + '//' + window.location.host; 
            navigator.clipboard.writeText(baseUrl + `/get_session/${data.session_id}`).then(()=>{
               
            }).catch(error => console.error('Error copying link', error));
        })
        .catch(error => console.error('Error saving session:', error));
    }

    openSharingModal()
    {
        this.saveSession();
        /*this.setState(prevState => ({
            sharingModalOpen: !prevState.sharingModalOpen
        }));*/
        this.handleSharingModalToggle();
    }

    copyLink() {
        
        this.saveSession();
    }
    
    shareOnLinkedIn()
    {
        const linkedinShareLink = `https://www.linkedin.com/shareArticle?mini=true&url=`;
        //const testLink = "https://verifai-project.com/";
        
        navigator.clipboard.readText().then(
            text => {
               // alert(text);
                let shareLink = linkedinShareLink + text; //+ testLink;   
        
                window.open(shareLink, '_blank');  
                      
            }
        ).catch(error => { alert("Error")});
      
        
       

    }

    shareOnFacebook()
    {
            
        const facebookShareLink = 'https://www.facebook.com/sharer/sharer.php?u='
       // const testLink = "https://verifai-project.com/";
        navigator.clipboard.readText().then(
            text => {
               // alert(text);
                const shareLink = facebookShareLink + text; //+ testLink;
                window.open(shareLink, '_blank');
            }
        ).catch(error => { alert("Error")});
      

    }

    shareOnTwitter()
    {
        
        const twitterShareLink = 'https://twitter.com/intent/tweet?url=';
        let title = null;
        let summary = null;
        
        if(this.state.questions.length != 0)

          {  title = this.state.questions[0].question; 
             summary = this.state.questions[0].result.substring(0, 100) + "... Check more at:"
             summary = summary.replace(/<[^>]*>/g, '');
           
            
          }

        navigator.clipboard.readText().then(
            text => {
               // alert(text);
                let shareLink = twitterShareLink + text;

                if(title && summary)
                {
                    shareLink += "&text=" + title + " " + summary;
                }

                window.open(shareLink, '_blank');
            }
        ).catch(error => { alert("Error")});


    }

    
    downloadDocument(path){
       //test_data\subfolder\2305.04928v4.pdf
        fetch(BACKEND + "download", {
            method: "POST",
            headers: {
                'Authorization': "Bearer " + this.context.user.token,
                'Content-Type': 'application/json',
                'Response-Type': 'blob'
            },
            body: JSON.stringify({file: path})
        }).then(async response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
    
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = path.split('\\').pop().split('/').pop() || 'downloadedFile';
            document.body.appendChild(a);
            a.click();

            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            alert("File downloading");

        }).catch(
            error => alert("Error downloading")
        )
        
    }


    

    postVerification(completeText) {
        const baseUrl = "https://pubmed.ncbi.nlm.nih.gov/";
        const document_found = this.state.questions[this.state.questions.length-1].document_found
       
        fetch(BACKEND + "verification_answer", {
            method: "POST",
            headers: {
                'Authorization': "Bearer " + this.context.user.token, 
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: completeText, document_found:document_found, stream: this.state.stream})
        })
        .then(async response => {
//        const data = await response.json();
//
//        if (data.message === "Verification is not enabled") {
//            // If verification is not enabled, return black color and empty text
//            return { text: completeText, color: "black" };
//            }

            function tooltipToWrite(listResult) {
                
                    
                let text = "";
                let color = "";
                for (let [pmid, result] of Object.entries(listResult)) {
                    
                    let label = result['label']
                  
                    if (color === "") {
                        color = (label === "SUPPORT") ? 'green' :
                                (label === "NO REFERENCE") ? 'gray' :
                                (label === "NO_EVIDENCE") ? 'orange' :
                                (label === "CONTRADICT") ? 'red' : '';
                    } else {
                        color = "blue"
                    }
            
                    let ballHtml = (label === "SUPPORT") ? '  <span class="green-ball"></span>' :
                                   (label === "NO REFERENCE") ? '  <span class="gray-ball"></span>' :
                                   (label === "NO_EVIDENCE") ? '  <span class="orange-ball"></span>' :
                                   (label === "CONTRADICT") ? '  <span class="red-ball"></span>' : '';
                    
                    let checkPmid;
                    let locationPath;
                    let foundDocument;

                    document_found.forEach(doc => {
                        if(doc.location === pmid)
                         {  
                             foundDocument = doc;
                             
                         }

                    })
                   


        
                    let tooltipText = (label === "SUPPORT" && foundDocument.pmid !== '') ? `The claim for document <a href=${baseUrl + pmid} target="_blank">PUBMED:${pmid}</a> is <strong>SUPPORT</strong>${ballHtml}` :
                                    (label === "SUPPORT" && foundDocument.pmid === '') ? (`The claim for document <a href="#" data-download="true">FILE:${foundDocument.location}</a> is <strong>SUPPORT</strong>${ballHtml}` ):
                                     (label === "NO REFERENCE") ? `The claim has <strong>NO REFERENCE</strong>${ballHtml}` :
                                     (label === "NO_EVIDENCE" && foundDocument.pmid !== '') ? `The claim for document <a href=${baseUrl + pmid}>PUBMED:${pmid}</a> has <strong>NO EVIDENCE</strong>${ballHtml}` :
                                     (label === "NO_EVIDENCE" && foundDocument.pmid === '') ? `The claim for document <a href="#" data-download="true">FILE:${foundDocument.location}</a> has <strong>NO EVIDENCE</strong>${ballHtml}` :
                                      (label === "CONTRADICT" && foundDocument.pmid !== '') ? `The claim for document <a href=${baseUrl + pmid}>PUBMED:${pmid}</a> has <strong>CONTRADICTION</strong>${ballHtml}` :
                                      (label === "CONTRADICT" && foundDocument.pmid === '') ? `The claim for document <a href="#" data-download="true">FILE:${foundDocument.location}</a> has <strong>CONTRADICTION</strong>${ballHtml}` : '';
                                      
                    if (label === "SUPPORT" || label === "CONTRADICT"){
                        let closest_sentence = result['closest_sentence']
                        tooltipText += `<br>Closest Sentence on the abstract: ${closest_sentence}`
                    }
                   
                    text += "<br>" + tooltipText;

                    
                }
                return { text: text, color: color };
            }


            
            
            function replacePubMedLinks(inputString) {
                
                const replaceWithLink = (match) => {
                   
                    const pubMedId = match.match(/\d+/)[0]; // Extract the number from the match
                    return `<a href="${baseUrl + pubMedId}" target="_blank">${match}</a>`;
                };
                
                let result = inputString.replace(MainScreen.regex, replaceWithLink);
                result = result.replace(MainScreen.regex_punct, replaceWithLink);
                
               
                result = result.replace(MainScreen.regex_square_brackets, replaceWithLink);
                 
               
                result = result.replace(MainScreen.regex_punct_2, replaceWithLink);
                result = result.replace(MainScreen.regex_punct_3, replaceWithLink);
            
                return result;
            }
            

            if (this.state.stream) {

                
            
            const readerVerification = response.body.getReader();
            const decoderVerification = new TextDecoder('utf-8');
              
            const processResultVerification = async (result) => {
                
                if (result.done) {
                      
                      this.setState(prevState => ({
                        questions: prevState.questions.map((q, i) => (
                            i === prevState.questions.length - 1 ? { ...q, status: "finished", loading:false} : q
                        )),
                    }), 
                    );

                    return;
                }
                
                // Any other operations if result.done is not true
                
               
                let claim_string = await decoderVerification.decode(result.value, {stream: true});
               
                //console.log("Arriva = ", claim_string)
                var claim_dict = JSON.parse(claim_string); // receiving the result from backend
                console.log("Result = ",claim_dict)
                console.log(typeof claim_dict);
              
                
                if (Object.keys(claim_dict).length === 0) {

                 
                    const ballHtml = ' <span class="gray-ball"></span>';
                    var color =  `<span class="tooltip" style="color: gray;">$1<span class="tooltiptext">The claim has <strong>NO REFERENCE</strong>${ballHtml}</span></span>`;
                    

                    const output = this.state.questions[this.state.questions.length - 1].result;
                    var final_output = `<span class="tooltip" style="color: gray;">${output}<span class="tooltiptext">The claim has <strong>NO REFERENCE</strong>${ballHtml}</span></span>`;

                   
                    
                    this.setState(prevState => ({
                        questions: prevState.questions.map((q, i) => (
                            i === prevState.questions.length - 1 ? { ...q, result: final_output, status: "finished", loading:false} : q
                        )),
                    }));
                    
                    return;
                }
                
             

                const { text: text_toolpit, color: color_to_use } = tooltipToWrite(claim_dict.result);

                
                var color =  `<span class="tooltip" style="color: ${color_to_use};">$1<span class="tooltiptext">${text_toolpit}</span></span>` 
                            
                
                var output = this.state.questions[this.state.questions.length - 1].result
                const regex_output = /<a\s+href=.*?>/gi;
                output = output.replace(regex_output, '');
                

                function escapeRegex(string) {
                    return string.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
                }
    
                function normalizeWhitespace(string) {
                    return string.replace(/\s+/g, ' ').trim();
                }
    

                // Function to highlight text in HTML
                function highlightText(html, textToHighlight, color) {
                    // Sanitize the HTML input
                    const safeHTML = DOMPurify.sanitize(html);
                    
                    // Split the claim text into sentences
                    const sentences = textToHighlight.match(/[^\.!\?]+[\.!\?]+/g) || [textToHighlight];
    
                    // Function to replace each sentence individually
                    function replaceSentence(html, sentence) {
                        // Escape special characters in the sentence
                        const escapedSentence = escapeRegex(normalizeWhitespace(sentence));
                        
    
                        // Create a regex pattern that handles whitespace and HTML tags between words
                     
                        const regexPattern = escapedSentence.split('\\s+').join('\\s*(?:<[^>]*>\\s*)*');
                      
                        const claim_regex = new RegExp(`(${regexPattern})`, 'gi');
                        
                        // Replace the matched text with the highlighted version
                        return html.replace(claim_regex, color);
                    }
                    // Process each sentence
                    let highlightedHTML = safeHTML;
                    if (sentences) {
                        sentences.forEach(sentence => {
                            console.log("Sentence = ", sentence);
                            highlightedHTML = replaceSentence(highlightedHTML, sentence);
                        });
                    }
    
                    
                    return highlightedHTML;
                }

                var highlightedHTML = highlightText(output, claim_dict.claim, color);
                

                highlightedHTML = replacePubMedLinks(highlightedHTML)
                    
                
                this.setState(prevState => ({
                    questions: prevState.questions.map((q, i) => (
                        i === prevState.questions.length - 1 ? { ...q, result: highlightedHTML } : q
                    ))
                }));

                return readerVerification.read().then(processResultVerification);
            };
    
            // Start reading the stream
            await readerVerification.read().then(processResultVerification);
        } else {
            
            const claim_dict_list_string = await response.json();

            const claim_dict_list = JSON.parse(claim_dict_list_string);

            const output = this.state.questions[this.state.questions.length - 1].result
            
            let html = DOMPurify.sanitize(output);

            console.log("Arriva questa lista = ", claim_dict_list);

            let i = 0
            for (const claim_dict of claim_dict_list) {
                
                function cleanHTML(inputText) {
                    // Regular expression to match tags that are not <span> or </span>
                    const regex = /<(?!\/?span\b)[^>]*>/gi;
                    
                    // Replace the matched parts with an empty string
                    return inputText.replace(regex, '');
                  }
                
                function normalizeWhitespace2(string) {
                    string = string.replace(/\s/g, ' ').trim();
                    return string.replace(/\s*([.,;!?:])\s*/g, '$1');
                }
                html = cleanHTML(html)
                html = normalizeWhitespace2(html)
                const { text: text_toolpit, color: color_to_use } = tooltipToWrite(claim_dict.result);
                console.log("text toolpit = ", text_toolpit)
                const color =  `<span class="tooltip" style="color: ${color_to_use};">${claim_dict.claim}<span class="tooltiptext">${text_toolpit}</span></span>` 
                
                
                
                //const claimRegex = new RegExp(claim_dict.claim.split(/\s+/).join('\\s*'), 'g');
               

                html = html.replace(normalizeWhitespace2(claim_dict.claim), color);
               
                console.log("HTML dopo = ", html);
                
                i = i + 1;
            }
            
            html = replacePubMedLinks(html)
            this.setState(prevState => ({
                questions: prevState.questions.map((q, i) => (
                    i === prevState.questions.length - 1 ? { ...q, result: html } : q
                ))
            }));

            this.setState(prevState => ({
                questions: prevState.questions.map((q, i) => (
                    i === prevState.questions.length - 1 ? { ...q, status: "finished", loading:false} : q
                )),
            }), 
            );
            }
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
        
        this.handleSaveQuestion();
        // First setState call with callback to execute after state is set
      
        this.setState(prevState => ({
            submitted: true,
            questions: [...prevState.questions, { 
                question: prevState.value, 
                result: "", 
                output_verification: "",
                status: "fetching_query", 
                loading: true, 
                document_found: {}, 
                showAllDocuments: false
            }]
        }), () => {
            // Call sendMessage function and use callback to update state
           
            this.sendMessage();
          
        });

      
    }

    
    setOutput(newOutput) {
       
        // Get the current state directly
        const questions = [...this.state.questions];
        var currentQuestion = questions[questions.length - 1];
        
        currentQuestion.result = currentQuestion.result + newOutput;

        this.setState({ questions });
    
    }
    
    setOutputVerification(newOutput) {
        
        //output_verification: prevState.output_verification  + newOutput
        const questions = [...this.state.questions];
        const currentQuestion = questions[questions.length - 1];
        currentQuestion.output_verification +=  newOutput;
        this.setState({ questions });
        return { questions };

    }
  
    setWrapperRef(node) {
        this.wrapperRef = node;
      }

    sharingModalRef(node)
    {
        this.sharingModal = node;
    }

    handleDownload = ({ file }) => {
    console.log("Downloading file:", file);
    fetch(`${BACKEND}download`, {
        method: 'POST',
        headers: {
            'Authorization': "Bearer " + this.context.user.token,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ file: file })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', file.split('/').pop()); // Use the last part of the URL as the filename
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error('Error downloading file:', error);
        alert('Error downloading file. Please try again.');
    });
};

  
        
      
    handleClickOutside(event) {
    if (this.wrapperRef && !this.wrapperRef.contains(event.target)) {
        this.setState({ modalOpen: false });
        }
    if (this.sharingModal && !this.sharingModal.contains(event.target)) {
            this.setState({ sharingModalOpen: false });
            }
        
    }

    handleCloseModal(event)
    {
        this.setState({ modalOpen: false });
    }
    hancleCloseSharingModal(event)
    {
        this.setState({ sharingModalOpen: false });
    }
    
    componentDidMount() {
      
        document.addEventListener('mousedown', this.handleClickOutside);
        document.addEventListener("click", this.handleDocumentClick);
       
      }
      
    componentWillUnmount() {
        document.removeEventListener('mousedown', this.handleClickOutside);
        document.removeEventListener("click", this.handleDocumentClick);
    
    }

    handleDocumentClick = (e) => {
        const target = e.target;
        // Check if the clicked element has `data-download="true"`
        if (target.matches('[data-download="true"]')) {
          e.preventDefault(); // Prevent default anchor behavior
         // this.downloadDocument(foundDocument);
         const filePath = target.textContent.replace("FILE:", "");
         this.downloadDocument(filePath);
        }
      };

    handleTooltip(index) {

        if (index >= this.state.questions.length) {
            throw new Error("Index out of bounds");
        } 
        console.log("ENTRO")
        const questions = [...this.state.questions];
        questions[index].showAllDocuments = !questions[index].showAllDocuments; 
        this.setState({questions})
        
    }
    
    
    render() {
        
        let isGetSession = false;
        return (
            <AuthContext.Consumer>
                
                {({ user, logout }) => {

                    
   
                    
                /*    if (!user) {

                        const currentPath = window.location.pathname.substring(1);
                
                        const handleLogin = () => {                     
                          this.props.navigate("/login/?redirection=" + currentPath);
                                       

                        }

                        if(currentPath === 'main')
            
                       { return (
                            <div className='App'>
                                <div className='login-message'>
                                    <img src={logo} alt="Logo" className="login-logo" />
                                    <div class='message-container'>
                                        <h1>Please log in to access this page.</h1>
                                        <button onClick={handleLogin}>Log in</button>
                                    </div>
                                </div>
                            </div>
                        );
                    } else {

                     return (
                        <div className='App'>
                         

                        </div>
                     );

                    }
                    } */
                    
                    const hasQuestions = this.state.questions && this.state.questions.length > 0;
                    const questionContent = hasQuestions ? this.state.questions[0] : '';
                    const description = hasQuestions ? questionContent.result.substring(0, 100) : '';
                    
                    
                    return (
                      <div  className='App'  ref={this.componentRef}>
                  
                     <div className={`MainScreenDiv ${this.state.loginModalOpen ? 'app-disabled' : ''}`}>
                     
                     <Helmet>
                            <meta property="og:title" content={ questionContent } />
                            <meta property="og:description" content={ description } />
                            <meta property="og:image" content={logo} />
                        

                      </Helmet> 
                            
                          
                        
                          <div className='MenuButtons'>
                          {user && (  <button title="User settings" className='UserButton' onClick={this.handleUserCredential}><div><p className='username' ref={this.usernameRef}>{user.username}</p></div></button>)}
                          {!user && (<div className='guestDiv'><p className='guest'>Guest</p></div>)}  
                            <div className='MenuButtonsSection'>
                                  
                       {user && ( <button title="Share" className="BlueButton" id="SharingButton" onClick={this.openSharingModal}>
                            <div className="button-content">
                                <img className="Share-logo" src={share}  />
                            
                            </div>
                        </button>)}
                        {user && (    <button title="Log out" className='LogoutButton' onClick={this.handleLogout}> <div className="button-content">
                                <img className="Logout-logo" src={logout_img}  />
                               
                            </div></button>)}
                        
                            {!user && (    <button title="Log in" className='LogoutButton' onClick={this.handleLogin}> <div className="button-content">
                               
                               <p>Log in</p>                         
                            </div></button>)}
                            
                      

                            </div>
                          

                        </div>
                       
                            
                           
                        {this.state.sharingModalOpen && (
                            <div className="SharingModalOverlay">
                            <div  className="SharingModalContent" ref={this.sharingModalRef}>
                            <div className='icon-container-share'><img className='close-icon' onClick={this.handleCloseSharingModal} src={close}/></div>
                            <div className="copiedMessage">
                            <img className="checkmark" src={checkmark}/>
                            <h1>Link copied</h1>

                            </div>
                            <div className='heading-container'>
                            <h1 id="share-heading">Share:</h1>
                            </div>

                            <div className='sharingContainer'>
                            <div className='sharing-options'>
                            
                            <button className="OptionButton" id="CopyLinkButton" onClick={this.copyLink}>
                                <div className="button-content">
                                    <img className="Option-logo" src={link}  />
                                    <p>Copy link</p>
                                </div>
                            </button>

                            <button className="OptionButton" id="LinkedInButton" onClick={this.shareOnLinkedIn}>
                                <div className="button-content">
                                    <img className="Option-logo" src={linkedin}  />
                                    <p>LinkedIn</p>
                                </div>
                            </button>
                        
                          
                           
                            <button className="OptionButton" id="FacebookButton" onClick={this.shareOnFacebook}>
                                <div className="button-content">
                                    <img className="Option-logo" src={facebook}  />
                                    <p>Facebook</p>
                                </div>
                            </button>
                            <button className="OptionButton" id="TwitterButton" onClick={this.shareOnTwitter}>
                                <div className="button-content">
                                    <img className="Option-logo" src={twitter}  />
                                    <p>Twitter</p>
                                </div>
                            </button>
                                
                            </div>
                        </div>
                        </div>
                        </div>
                        )}
                        
                            <div className="router-reset">

                              <div className="LogoContainer">
                              <img className="App-logo" src={logo} alt="Logo" />
                                

                                </div>  
                                <div className='websiteLinkDiv'>  <a className='websiteLink' href="https://verifai-project.com/">Verif.ai Project Website</a>
                                </div>
                              
                                <div className="InputQuestion">
                                    <div className='tabbed'>
                                        <label id="inputMessage" htmlFor="question">
                                            Input your question in natural language:
                                        </label>
                                        <br/>
                                    </div>
                                   

                                   <div className='QuestionSection'>
                                   <button id="settings-btn" onClick={this.handleModalToggle} aria-label="Settings"><div className="circleButtonContent"><img className="SettingsLogo" src={new_settings}/></div></button>
                                  
                                  
                                    <form onSubmit={this.handleSubmit} className='QuestionClassForm'>
                                  
                                  {!user && (  <input
                                            id="question"
                                            name="question"
                                            className="QuestionClass"
                                            placeholder="e.g. What genes are promising targets for prostate cancer?"
                                            value={this.state.value}
                                            onChange={this.handleChange}
                                            ref = {this.questionRef}
                                            onClick={this.handleLoginModalToggle}
                                        />
                                    )}

                                    {user && (  <input
                                            id="question"
                                            name="question"
                                            className="QuestionClass"
                                            placeholder="e.g. What genes are promising targets for prostate cancer?"
                                            value={this.state.value}
                                            onChange={this.handleChange}
                                            ref = {this.questionRef}
                                          
                                        />
                                    )}

                                    
                                      
                                        <button className='AskButton' onClick={this.handleSubmit}>
                                            <div className="circleButtonContent">
                                                <img className="AskLogo" src={ask}/>
                                            </div>
                                        </button>
                                    </form>
                                </div>
                                </div>
                                <div className="search-area">
                                       
                                       {this.state.modalOpen && (
                                           <div className="ModalContent" ref={this.setWrapperRef}>
                                            <div className='icon-container'><img className='close-icon' onClick={this.handleCloseModal} src={close}/></div>
                                               <div className='modal-title'><h2>Search Configuration</h2></div>
                                               <div className='SearchConfiguration'>
                                                <div className='search-section'>
                                               <label id="type-search">Type of Search:
                                                 
                                                 
                                               </label>
                                               <select className='combobox' id="search-options" value={this.state.search_type} onChange={this.handleSearchTypeChange}>
                                                       <option value="hybrid">Hybrid</option>
                                                       <option value="lexical">Lexical</option>
                                                       <option value="semantic">Semantic</option>
                                                   </select>
                                                   </div>
                                               </div>
                                               {this.state.search_type === 'hybrid' && (
                                                <div className="WeightsConfiguration">
                                                   <div className="weight-labels">
                                                       <label>
                                                           Lexical Weights: {this.state.lex_parameter.toFixed(3)}, Semantic Weights: {(1 - this.state.lex_parameter).toFixed(3)}
                                                           <div className="weight-input">
                                                           <div className='weightSliderContainer'>
                                                           <input className='slider'
                                                               type="range" 
                                                               min="0" 
                                                               max="1" 
                                                               value={this.state.lex_parameter}
                                                               step="0.01"
                                                               onChange={this.handleLexParamChange}
                                                           />
                                                           </div>
                                                           <div className='weight-btn-container'>
                                                           <div className='weight-buttons'>
                                                           <button className="weight-label start" onClick={() => this.setState({ lex_parameter: 0.3, sem_parameter: 0.7 })}>SEMANTIC</button>
                                                           <button className="weight-label middle" onClick={() => this.setState({ lex_parameter: 0.5, sem_parameter: 0.5 })}>NEUTRAL</button>
                                                           <button className="weight-label end" onClick={() => this.setState({ lex_parameter: 0.7, sem_parameter: 0.3 })}>LEXICAL</button>
                                                           </div>
                                                           </div>
                                                           </div>
                                                       </label>
                                                   </div>
                                                   </div>
                                               )}
                                               
                                               <div className='DocumentNumConfiguration'>
                                               <label>Number of Documents: 
                                               </label>
                                               <select className='combobox'
                                                       value={this.state.numDocuments}
                                                       onChange={this.handleNumDocumentsChange}
                                                       title="Please select the number of documents"
                                                   >
                                                       <option value="10">Normal - 10 documents</option>
                                                       <option value="5">Small - 5 documents</option>
                                                       <option value="15">Large - 15 documents</option>
                                                       <option value="20">Extra Large - 20 documents</option>
                                                   </select>
                                               </div>
                                               <div className='DateConfiguration'>
                                               <div className="date-picker-group">
                                                   <label htmlFor="start">From:</label>
                                                   <input className='datepicker'
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
                                                   <input className="datepicker"
                                                       type="date"
                                                       id="end"
                                                       name="trip-end"
                                                       value={this.state.endDate}
                                                       onChange={this.handleEndDateChange}
                                                       min={this.state.startDate}
                                                       max="2030-01-01"
                                                   />
                                               </div>
                                               </div>
                                               <div className='WeightsConfiguration'>
                                               <div className="weight-labels">
                                               <label>Temperature: {this.state.temperature}:
                                                  <div className='temperature-desc'> <p>The higher the temperature, the less accurate answers will be.</p></div>
                                                   <div className='weightSliderContainer'>
                                                   <input id="tempSlider" className='slider'
                                                       type="range"
                                                       value={this.state.temperature}
                                                       min="0"
                                                       max="1"
                                                       step="0.01"
                                                       onChange={this.handleTemperatureChange}
                                                   />
                                                   </div>
                                                   <div className='weight-btn-container'>
                                                   <div className='weight-buttons'>
                                                   <button className="weight-label start" onClick={() => this.setState({ temperature: '0' })}>PRECISE</button>
                                                   <button className="weight-label middle" onClick={() => this.setState({ temperature: '0.5' })}>NEUTRAL</button>
                                                   <button className="weight-label end" onClick={() => this.setState({ temperature: '1' })}>CREATIVE</button>
                                                   </div>
                                                   </div>
                                               </label>
                                           </div>
                                           </div>
                                               
                                           <div id="StreamConfiguration" className='SearchConfiguration'>
                                           <div className='search-section'>
                                           <label>Stream:
                                           </label>
                                           <select className='combobox'
                                                   value={this.state.stream}
                                                   onChange={this.handleStreamChange}
                                                   title="Please select the stream option"
                                               >
                                                   <option value="true">Stream</option>
                                                   <option value="false">Not Stream</option>
                                               </select>
                                           </div>
                                           </div>
                                           </div>
                                   )}
                                <br></br>
                                {this.state.questions.slice().reverse().map((q, index) => (
                                
                            <div className="Answer">
                                <div className="AnswerContainer" key={index}>
                                <h1>{q.question}</h1>
                                   
                                    
                                    <br></br>
                                    
                                
                                   
                                    <div className="sources-section">
                                    <h2>Sources:</h2>
                                        <div className="document-section">
                                        {q.document_found && Object.keys(q.document_found)
                                        .slice(0, q.showAllDocuments ? Object.keys(q.document_found).length : 5)
                                        .map((i) => {
                                            const baseUrl = "https://pubmed.ncbi.nlm.nih.gov/";
                                            const doc = q.document_found[i];

                                            try {
                                                const pmid = doc.pmid;
                                                const location = doc.location;
                                                const title = doc.text.split('\n\n')[0];
                                                const content = doc.text.replace(title, '').trim();
                                                const truncatedContent = content.length > 100 ? content.substring(0, 100) + '...' : content;
                                                const truncatedTitle = title.length > 50 ? title.substring(0, 50) + '...' : title;
                                                const docUrl = baseUrl + pmid;
                                                
                                                
                                                return (
                                                    <div>
                                                        {doc.pmid === '' && (
                                                    <a href="#"  onClick={() => this.downloadDocument(doc.location)} key={i} className="no-underline-link">
                                                        <div className="document-square">
                                                            <h3 className="document-title">{truncatedTitle}</h3>
                                                            <p className="document-content">{truncatedContent}</p>
                                                        </div>
                                                    </a>
                                                    )} : {doc.pmid !== '' && (
                                                        <a href="{docUrl}" key={i} target="_blank" rel="noopener noreferrer" className="no-underline-link">
                                                        <div className="document-square">
                                                            <h3 className="document-title">{truncatedTitle}</h3>
                                                            <p className="document-content">{truncatedContent}</p>
                                                        </div>
                                                    </a>

                                                    )}

                                                    </div>
                                                );
                                            } catch (error) {
                                                console.error("Error processing document:", error);
                                                return null;
                                            }
                                        })
                                    }
                                        {!q.showAllDocuments && Object.keys(q.document_found).length > 5 && (
                                        <div className="document-square center" onClick={() => this.handleTooltip(this.state.questions.length - 1 - index)}>  
                                            <h3 className="document-title">
                                                {`View ${Object.keys(q.document_found).length - 5} more`}
                                            </h3>
                                        </div>
                                    )}
                                   
                                    </div>
                                    </div>
                                    
                                  
                                    
                                    <br></br>

                                  
                                    {Object.keys(q.document_found).length > 0 && (
                                    <h2 className="StatusMessage">
                                        {q.status === "fetching_query" && "Answering"}
                                        {q.status === "fetching_verification" && "Verification"}
                                        {q.status !== "fetching_verification" && q.status !== "fetching_query" && "Answer:"}
                                        {q.loading && <div className="spinner" />}
                                    </h2>
                                    )}
                                  
                            
                               
                               
                                <div className="output-section">
                                    <div className="output-tokens" dangerouslySetInnerHTML={{ __html: q.result }} />
                                </div>

                           
                            </div>
                            </div>
                                ))}
                            </div>
                        </div>
                        </div>
                        {this.state.loginModalOpen && (<>
                        <div className='LoginModalOverlay'>
                        </div>
                        <div className='LoginModal'>
                          
                           
                            <div className="login-form">
                                <div className='closeDiv'><img className='close-icon' onClick={this.handleLoginModalToggle} src={close}/></div>
                                <h1>Sign in</h1>
                                <form className="formClass">
                                    <input onChange={this.handleUsernameChange} className="formInput" type="text" placeholder="Username" />
                                    <input onChange={this.handlePasswordChange}  className="formInput" type="password" placeholder="Password" />
                                    <button onClick={this.formLogin} class="center-button">Log In</button>
                                </form>
                                
                            
                            <br></br>
                            <p className='message'>New to VerifAi app? <targe><span onClick={this.formRegister} style={{ color: '#23a1ee', cursor: 'pointer' }}>Sign up</span></targe> to get instant access.</p>
                        
                        </div>
                                
                         
                            

                        </div>
                        
                        </>
                    )}
                        </div>
                        
                    
                );
            }}
        </AuthContext.Consumer>
    );
}
}

export default NavigateWrapper;
//export default MainScreen;