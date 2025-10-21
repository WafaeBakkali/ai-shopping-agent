import React, { useState, useRef } from 'react';
import { Sparkles, Upload, Loader2, ShoppingBag, Check, X } from 'lucide-react';
import './index.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

export default function App() {
  const [prompt, setPrompt] = useState('');
  const [step, setStep] = useState('prompt');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedItems, setSelectedItems] = useState([]);
  const [userPhoto, setUserPhoto] = useState(null);
  const [tryonResults, setTryonResults] = useState({});
  const [videoResult, setVideoResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [aiThinking, setAiThinking] = useState('');
  
  const fileInputRef = useRef(null);

  const examplePrompts = [
    "I need a woman's outfit for a job interview for under 300 euros",
    "I'm looking for a dress for a birthday party under 100 euros",
    "I need a man's outfit for a job interview for under 300 euros",
    "I need a mid-century modern look for my living room under $2000",
    "Show me wireless headphones for running",
  ];

  // Calculate total price of selected items
  const calculateTotal = () => {
    return selectedItems.reduce((total, item) => {
      const priceStr = item.price.replace(/[^\d,.-]/g, '').replace(',', '.');
      const price = parseFloat(priceStr) || 0;
      return total + price;
    }, 0);
  };

  const handleSubmit = async () => {
    if (!prompt.trim()) return;

    setIsLoading(true);
    setStep('searching');
    setLoadingMessage('Analyzing your request...');
    
    const thinkingMessages = [
      'Understanding your query...',
      'Detecting items to search...',
      'Preparing to browse Amazon...',
      'Comparing products...',
      'Extracting details...'
    ];
    
    let msgIndex = 0;
    const thinkingInterval = setInterval(() => {
      if (msgIndex < thinkingMessages.length) {
        setAiThinking(thinkingMessages[msgIndex]);
        msgIndex++;
      }
    }, 2500);

    try {
      const response = await fetch(`${API_URL}/advanced-search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt })
      });
      
      clearInterval(thinkingInterval);
      const data = await response.json();
      
      setSearchResults(data.products || []);
      setStep('results');
    } catch (error) {
      clearInterval(thinkingInterval);
      alert('Search failed: ' + error.message);
    } finally {
      setIsLoading(false);
      setAiThinking('');
    }
  };

  const toggleItemSelection = (item) => {
    if (selectedItems.find(i => i.id === item.id)) {
      setSelectedItems(selectedItems.filter(i => i.id !== item.id));
    } else {
      setSelectedItems([...selectedItems, item]);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => setUserPhoto(e.target.result);
      reader.readAsDataURL(file);
    }
  };

  const handleTryOnAll = async () => {
    if (!userPhoto) {
      alert('Please upload your photo first!');
      return;
    }
    
    if (selectedItems.length === 0) {
      alert('Please select at least one item!');
      return;
    }
    
    setIsLoading(true);
    setLoadingMessage(`Creating your virtual try-on...`);
    
    const thinkingMessages = [
      'Analyzing your photo...',
      selectedItems.length > 2 ? 'Creating product collage...' : 'Processing images...',
      'Generating photorealistic try-on...',
      'Applying lighting effects...',
      'Finalizing your outfit...'
    ];
    
    let msgIndex = 0;
    const thinkingInterval = setInterval(() => {
      if (msgIndex < thinkingMessages.length) {
        setAiThinking(thinkingMessages[msgIndex]);
        msgIndex++;
      }
    }, 2000);
    
    try {
      const response = await fetch(`${API_URL}/tryon`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_photo: userPhoto,
          items: selectedItems.map(item => ({
            name: item.name,
            price: item.price,
            image_url: item.image_url || item.image
          }))
        })
      });
      
      clearInterval(thinkingInterval);
      const data = await response.json();
      
      if (data.success && data.result_image) {
        setTryonResults({
          combined: data.result_image,
          items_count: data.items_count
        });
        setStep('tryon');
      } else {
        throw new Error(data.error || 'No image received');
      }
    } catch (error) {
      clearInterval(thinkingInterval);
      alert('Try-on generation failed: ' + error.message);
    } finally {
      setIsLoading(false);
      setAiThinking('');
    }
  };

  const handleGenerateVideo = async () => {
    if (!tryonResults.combined) {
      alert('Please generate a try-on first!');
      return;
    }
    
    setIsLoading(true);
    setLoadingMessage('Creating your video...');
    
    const thinkingMessages = [
      'Analyzing outfit...',
      'Generating camera movements...',
      'Adding effects...',
      'Rendering video...',
      'Almost ready...'
    ];
    
    let msgIndex = 0;
    const thinkingInterval = setInterval(() => {
      if (msgIndex < thinkingMessages.length) {
        setAiThinking(thinkingMessages[msgIndex]);
        msgIndex++;
      }
    }, 3000);
    
    try {
      const response = await fetch(`${API_URL}/generate-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_photo: tryonResults.combined,
          items: selectedItems.map(item => ({
            name: item.name,
            price: item.price,
            image_url: item.image_url || item.image
          }))
        })
      });
      
      clearInterval(thinkingInterval);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Video generation failed');
      }
      
      const data = await response.json();
      
      if (data.success && data.video_url) {
        setVideoResult(data.video_url);
        setStep('video');
      } else {
        throw new Error(data.error || 'Video generation failed');
      }
    } catch (error) {
      clearInterval(thinkingInterval);
      alert('Video generation failed: ' + error.message);
      setStep('tryon');
    } finally {
      setIsLoading(false);
      setAiThinking('');
    }
  };

  const handlePurchase = async () => {
    setIsLoading(true);
    setLoadingMessage('Processing checkout...');
    
    try {
      const response = await fetch(`${API_URL}/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          items: selectedItems,
          user_info: {
            name: 'Demo User',
            email: 'demo@example.com'
          }
        })
      });
      
      await response.json();
      setStep('checkout');
    } catch (error) {
      alert('Purchase failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const reset = () => {
    setPrompt('');
    setStep('prompt');
    setSearchResults([]);
    setSelectedItems([]);
    setUserPhoto(null);
    setTryonResults({});
    setVideoResult(null);
  };

  return (
    <div className="min-h-screen bg-black">
      {isLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50 backdrop-blur-sm">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 shadow-2xl max-w-md mx-4">
            <Loader2 className="animate-spin text-white mx-auto mb-4" size={56} />
            <p className="text-lg font-semibold text-white text-center mb-2">{loadingMessage}</p>
            {aiThinking && (
              <div className="mt-3 p-3 bg-zinc-800 rounded-lg border border-zinc-700">
                <p className="text-sm text-zinc-300 text-center animate-pulse font-medium">
                  {aiThinking}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="text-center mb-12 pt-8">
          <div className="inline-flex items-center gap-3 bg-zinc-900 border border-zinc-800 px-6 py-3 rounded-full mb-4">
            <Sparkles className="text-yellow-400" size={24} />
            <span className="text-white font-semibold">Powered by Google Gemini 2.5 Computer Use • Gemini 2.5 Flash Image (Nano Banana) • Veo</span>
          </div>
          <h1 className="text-5xl font-bold text-white mb-3 tracking-tight">
            AI Shopping Assistant
          </h1>
          <p className="text-zinc-400 text-lg mb-2">
            Created by Wafae Bakkali
          </p>
        </div>

        {step === 'prompt' && (
          <div className="max-w-3xl mx-auto">
            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl overflow-hidden">
              <div className="p-8">
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="What are you looking for? Try 'outfit for a wedding' or 'running shoes under 150'"
                  className="w-full px-6 py-4 text-lg bg-black border-2 border-zinc-800 rounded-xl text-white placeholder-zinc-500 focus:border-zinc-600 focus:ring-4 focus:ring-zinc-800 resize-none"
                  rows="4"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit();
                    }
                  }}
                />
                
                <button
                  onClick={handleSubmit}
                  disabled={!prompt.trim()}
                  className="w-full mt-4 px-8 py-4 bg-white text-black rounded-xl font-semibold text-lg hover:bg-zinc-200 disabled:bg-zinc-800 disabled:text-zinc-600 disabled:cursor-not-allowed shadow-lg transform transition hover:scale-105"
                >
                  <Sparkles className="inline mr-2" size={20} />
                  Search with AI
                </button>
              </div>

              <div className="bg-black px-8 py-6 border-t border-zinc-800">
                <p className="text-sm text-zinc-400 mb-3 font-medium">Try these:</p>
                <div className="space-y-2">
                  {examplePrompts.map((example, idx) => (
                    <button
                      key={idx}
                      onClick={() => setPrompt(example)}
                      className="block w-full text-left px-4 py-2 text-sm text-zinc-300 bg-zinc-900 rounded-lg hover:bg-zinc-800 transition border border-zinc-800"
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {step === 'results' && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl p-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white">
                  Found {searchResults.length} items
                </h2>
                <p className="text-sm text-zinc-400 mt-1">
                  Select items for virtual try-on
                </p>
              </div>
              <button onClick={reset} className="text-zinc-400 hover:text-white">
                <X size={24} />
              </button>
            </div>

            {searchResults.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-zinc-400 text-lg">No products found. Try a different search.</p>
                <button
                  onClick={reset}
                  className="mt-4 px-6 py-3 bg-white text-black rounded-lg hover:bg-zinc-200"
                >
                  Try Again
                </button>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  {searchResults.map((item, idx) => (
                    <div
                      key={idx}
                      onClick={() => toggleItemSelection({...item, id: idx})}
                      className={`border-2 ${selectedItems.find(i => i.id === idx) ? 'border-white bg-zinc-800' : 'border-zinc-800'} rounded-xl overflow-hidden cursor-pointer hover:shadow-lg hover:border-zinc-600 transition`}
                    >
                      <img 
                        src={item.image || item.image_url || 'https://via.placeholder.com/300x400'} 
                        alt={item.name} 
                        className="w-full h-48 object-contain bg-black"
                        onError={(e) => {
                          e.target.src = 'https://via.placeholder.com/300x400?text=No+Image';
                        }}
                      />
                      <div className="p-3 bg-zinc-900">
                        <p className="font-medium text-sm text-white line-clamp-2">{item.name}</p>
                        <p className="text-white font-bold mt-1">{item.price}</p>
                        {selectedItems.find(i => i.id === idx) && (
                          <div className="mt-2 flex items-center gap-1 text-white text-xs font-medium">
                            <Check size={14} />
                            Selected
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="bg-black border border-zinc-800 rounded-xl p-4 mb-4">
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-400">Total Price:</span>
                    <span className="text-white text-xl font-bold">{calculateTotal().toFixed(2)} €</span>
                  </div>
                  <p className="text-zinc-500 text-xs mt-1">{selectedItems.length} item{selectedItems.length !== 1 ? 's' : ''} selected</p>
                </div>

                <button
                  onClick={() => setStep('tryon-upload')}
                  disabled={selectedItems.length === 0}
                  className="w-full px-8 py-4 bg-white text-black rounded-xl font-semibold text-lg hover:bg-zinc-200 disabled:bg-zinc-800 disabled:text-zinc-600 shadow-lg"
                >
                  Try On ({selectedItems.length} item{selectedItems.length !== 1 ? 's' : ''})
                </button>
              </>
            )}
          </div>
        )}

        {step === 'tryon-upload' && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl p-8 max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold text-white mb-2">Upload your photo</h2>
            <p className="text-zinc-400 mb-2">
              See yourself wearing all {selectedItems.length} item{selectedItems.length !== 1 ? 's' : ''} together
            </p>
            <div className="mb-6 p-3 bg-black border border-zinc-800 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-zinc-400 text-sm">Total Outfit Price:</span>
                <span className="text-white text-lg font-bold">{calculateTotal().toFixed(2)} €</span>
              </div>
            </div>
            
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-zinc-700 rounded-xl h-80 flex items-center justify-center cursor-pointer hover:border-zinc-600 transition mb-6 bg-black"
            >
              {userPhoto ? (
                <img src={userPhoto} alt="You" className="max-h-full rounded-xl" />
              ) : (
                <div className="text-center">
                  <Upload className="mx-auto mb-3 text-zinc-600" size={64} />
                  <p className="text-zinc-300 font-medium">Click to upload</p>
                  <p className="text-sm text-zinc-500 mt-1">Best with front-facing photos</p>
                </div>
              )}
            </div>
            <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFileUpload} className="hidden" />

            <div className="flex gap-4">
              <button
                onClick={() => setStep('results')}
                className="flex-1 px-6 py-3 border-2 border-white text-white rounded-xl font-semibold hover:bg-zinc-800"
              >
                Back
              </button>
              <button
                onClick={handleTryOnAll}
                disabled={!userPhoto}
                className="flex-1 px-8 py-4 bg-white text-black rounded-xl font-semibold text-lg disabled:bg-zinc-800 disabled:text-zinc-600 shadow-lg hover:bg-zinc-200"
              >
                Generate Try-On
              </button>
            </div>
          </div>
        )}

        {step === 'tryon' && tryonResults.combined && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl p-8">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-2xl font-bold text-white">Your Virtual Try-On</h2>
              <div className="text-right">
                <div className="text-white text-2xl font-bold">{calculateTotal().toFixed(2)} €</div>
                <div className="text-zinc-400 text-sm">Total Price</div>
              </div>
            </div>
            <p className="text-zinc-400 mb-6">
              Generated with {tryonResults.items_count} item{tryonResults.items_count !== 1 ? 's' : ''}
            </p>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-6">
              <div className="rounded-xl overflow-hidden shadow-lg border border-zinc-800">
                {tryonResults.combined ? (
                  <img 
                    src={tryonResults.combined} 
                    alt="Virtual try-on result" 
                    className="w-full"
                  />
                ) : (
                  <div className="w-full h-96 bg-zinc-800 flex items-center justify-center">
                    <p className="text-zinc-500">Loading try-on result...</p>
                  </div>
                )}
                <div className="p-4 bg-black">
                  <p className="font-semibold text-white">AI-Generated Result</p>
                  <p className="text-sm text-zinc-400">{tryonResults.items_count} item{tryonResults.items_count !== 1 ? 's' : ''} styled</p>
                </div>
              </div>
              
              <div className="space-y-4">
                <h3 className="font-semibold text-white mb-3">Items in this outfit:</h3>
                {selectedItems.map((item, idx) => (
                  <div key={idx} className="flex items-center gap-4 p-3 bg-black border border-zinc-800 rounded-lg">
                    <img 
                      src={item.image || item.image_url} 
                      alt={item.name}
                      className="w-16 h-16 object-contain rounded bg-zinc-900"
                      onError={(e) => e.target.src = 'https://via.placeholder.com/64'}
                    />
                    <div className="flex-1">
                      <p className="font-medium text-sm text-white line-clamp-2">{item.name}</p>
                      <p className="text-white font-bold text-sm">{item.price}</p>
                    </div>
                    <Check className="text-green-500" size={20} />
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-4">
              <button
                onClick={() => {
                  setTryonResults({});
                  setStep('results');
                }}
                className="flex-1 px-6 py-3 border-2 border-white text-white rounded-xl font-semibold hover:bg-zinc-800"
              >
                Try Different Items
              </button>
              <button
                onClick={handleGenerateVideo}
                className="flex-1 px-6 py-3 bg-white text-black rounded-xl font-semibold shadow-lg hover:bg-zinc-200"
              >
                🎬 Create Video
              </button>
            </div>
          </div>
        )}

        {step === 'video' && videoResult && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl p-8 max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold text-white mb-2">Your Video</h2>
            <p className="text-zinc-400 mb-4">AI-generated with Veo 3.1</p>
            
            <div className="relative mx-auto mb-6" style={{ width: 'min(100%, 450px)' }}>
              <video 
                controls 
                className="w-full rounded-xl shadow-lg bg-black border border-zinc-800" 
                style={{ aspectRatio: '9/16' }}
                src={videoResult}
              ></video>
            </div>
            
            <div className="flex gap-4">
              <button
                onClick={() => setStep('tryon')}
                className="flex-1 px-6 py-3 border-2 border-white text-white rounded-xl font-semibold hover:bg-zinc-800"
              >
                Back
              </button>
              <button
                onClick={handlePurchase}
                className="flex-1 px-8 py-4 bg-white text-black rounded-xl font-semibold text-lg shadow-lg hover:bg-zinc-200"
              >
                <ShoppingBag className="inline mr-2" size={24} />
                Complete Purchase
              </button>
            </div>
          </div>
        )}

        {step === 'checkout' && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl p-12 max-w-2xl mx-auto text-center">
            <div className="w-20 h-20 bg-green-500 bg-opacity-20 rounded-full flex items-center justify-center mx-auto mb-6 border-2 border-green-500">
              <Check className="text-green-500" size={40} />
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">Order Complete!</h2>
            <p className="text-zinc-400 text-lg mb-8">
              Successfully processed {selectedItems.length} item{selectedItems.length !== 1 ? 's' : ''}
            </p>
            <button
              onClick={reset}
              className="px-8 py-4 bg-white text-black rounded-xl font-semibold shadow-lg hover:bg-zinc-200"
            >
              Start New Search
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
