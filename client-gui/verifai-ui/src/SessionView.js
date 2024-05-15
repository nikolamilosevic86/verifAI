import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

function SessionView() {
    const { sessionId } = useParams();
    const [content, setContent] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const url = `http://3.74.47.54:5001/get_session/${sessionId}`;
        fetch(url)
            .then(response => response.json())
            .then(data => {
                // Pass an array of selectors for classes to remove
                function removeSpecificDiv(htmlContent, selectors) {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(htmlContent, 'text/html');
                
                    // Iterate over all selectors and remove elements
                    selectors.forEach(selector => {
                        const elementsToRemove = doc.querySelectorAll(selector);
                        elementsToRemove.forEach(element => {
                            element.remove();
                        });
                    });
                
                    // Serialize the document back to string
                    return doc.body.innerHTML;
                }
                const modifiedContent = removeSpecificDiv(data.html, ['.search-area','.tabbed']);
                setContent(modifiedContent);
            })
            .catch(error => console.error('Error fetching data:', error));
    }, [sessionId]);

    const handleNavigateMain = () => {
        navigate('/main');  // Navigate to the main page
    };
    return (
        <div>
            <button class="simpleBlueButton" onClick={handleNavigateMain}>Go to Main</button>  
            <div dangerouslySetInnerHTML={{ __html: content }} />
            
        </div>
    );
}

export default SessionView;
