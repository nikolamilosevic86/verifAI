
from datasets import DatasetDict


def split_fixed(dataset,fixed_test_size:int=50,train_size:float=0.9,seed=42):

    assert train_size, "The split must be lower or equal than 1"

    idxs_range = range(len(dataset['train'])-fixed_test_size, len(dataset['train']))
    test_dataset = dataset['train'].select(idxs_range)
    train_val_dataset = dataset['train'].select(range(len(dataset['train'])-fixed_test_size)).train_test_split(test_size=1-train_size, seed=seed) 

    return DatasetDict({
        'train': train_val_dataset['train'],
        'val':train_val_dataset['test'],
        'test': test_dataset
    })


def split(dataset,train_size:float=0.8,val_size:float=0.1,seed=42):

    assert train_size+val_size<=1, "The split must be lower or equal than 1"

    train_test_val = dataset["train"].train_test_split(test_size=1-train_size, seed=seed)
    test_val = train_test_val["test"].train_test_split(test_size=1-(val_size/(1-train_size)), seed=seed)
    return DatasetDict({
        'train': train_test_val['train'],
        'val': test_val['train'],
        'test': test_val['test']
    })

def tokenize_dataset(dataset,
                     tokenizer,
                     input_key:str="input",
                     target_key:str="target",
                     input_preprocess=None,
                     target_preprocess=None
                     ):

    """
    Function that takes in input:
        - dataset: (splitted) string dataset with an input string and a label string
        - tokenizer: an huggingface tokenizer
        - input_key: the key of the dataset correspoding to the input string
        - target_key: the key of the dataset correspoding to the label string

        Optional preprocessing functions applied to the whole dataset:
        - input_preprocess: a function that take a single input string as input and output a preprocessed verions of it
        - target_preprocess: a function that take a target string as input and output a preprocessed verions of it

    Returns a tokenized dataset dict
    """

    def batch_tokenize_target(examples:list):

        if input_preprocess == None: inputs = [example for example in examples[input_key]]
        else: inputs = [input_preprocess(example) for example in examples[input_key]]
        
        if target_preprocess == None: targets = [example for example in examples[target_key]]
        else: targets = [target_preprocess(example) for example in examples[target_key]]

        model_inputs = tokenizer(inputs)
        labels = tokenizer(text_target=targets)

        model_inputs["labels"] = labels["input_ids"]

        return model_inputs

    def batch_tokenize(examples:list):

        if input_preprocess == None: inputs = [example for example in examples[input_key]]
        else: inputs = [input_preprocess(example) for example in examples[input_key]]

        model_inputs = tokenizer(inputs)

        return model_inputs

    if "target" in dataset["train"].features:
        return dataset.map(batch_tokenize_target, batched=True)
    else:
        return dataset.map(batch_tokenize, batched=True)
