from typing import Callable, List, Union

import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem


Molecule = Union[str, Chem.Mol, List[List[str]], List[List[Chem.Mol]]]
FeaturesGenerator = Callable[[Molecule], np.ndarray]


FEATURES_GENERATOR_REGISTRY = {}


def register_features_generator(features_generator_name: str) -> Callable[[FeaturesGenerator], FeaturesGenerator]:
    """
    Creates a decorator which registers a features generator in a global dictionary to enable access by name.

    :param features_generator_name: The name to use to access the features generator.
    :return: A decorator which will add a features generator to the registry using the specified name.
    """
    def decorator(features_generator: FeaturesGenerator) -> FeaturesGenerator:
        FEATURES_GENERATOR_REGISTRY[features_generator_name] = features_generator
        return features_generator

    return decorator


def get_features_generator(features_generator_name: str) -> FeaturesGenerator:
    """
    Gets a registered features generator by name.

    :param features_generator_name: The name of the features generator.
    :return: The desired features generator.
    """
    if features_generator_name not in FEATURES_GENERATOR_REGISTRY:
        raise ValueError(f'Features generator "{features_generator_name}" could not be found. '
                         f'If this generator relies on rdkit features, you may need to install descriptastorus.')

    return FEATURES_GENERATOR_REGISTRY[features_generator_name]


def get_available_features_generators() -> List[str]:
    """Returns a list of names of available features generators."""
    return list(FEATURES_GENERATOR_REGISTRY.keys())


MORGAN_RADIUS = 2
MORGAN_NUM_BITS = 2048


@register_features_generator('morgan')
def morgan_binary_features_generator(mol_data: Union[Molecule, List[Molecule]],
                                     radius: int = MORGAN_RADIUS,
                                     num_bits: int = MORGAN_NUM_BITS) -> np.ndarray:
    """
    Generates a binary Morgan fingerprint for a molecule.
    :param mol_data: A molecule (i.e., either a SMILES or an RDKit molecule).
    :param radius: Morgan fingerprint radius.
    :param num_bits: Number of bits in Morgan fingerprint.
    :return: A 1D numpy array containing the binary Morgan fingerprint.
    """

    if type(mol_data) == list:
        features = []
        for datapoint in mol_data:
            entry_features = []
            for molecule in datapoint:
                molecule = Chem.MolFromSmiles(molecule) if type(molecule) == str else molecule
                features_vec = AllChem.GetMorganFingerprintAsBitVect(molecule, radius, nBits=num_bits)
                f = np.zeros((1,))
                DataStructs.ConvertToNumpyArray(features_vec, f)
                entry_features.append(f)
            features.extend(entry_features)
        features = np.array(features)
    else:
        mol_data = Chem.MolFromSmiles(mol_data) if type(mol_data) == str else mol_data
        features_vec = AllChem.GetMorganFingerprintAsBitVect(mol_data, radius, nBits=num_bits)
        features = np.zeros((1,))
        DataStructs.ConvertToNumpyArray(features_vec, features)

    return features


@register_features_generator('morgan_count')
def morgan_counts_features_generator(mol_data: Union[Molecule, List[Molecule]],
                                     radius: int = MORGAN_RADIUS,
                                     num_bits: int = MORGAN_NUM_BITS) -> np.ndarray:
    """
    Generates a counts-based Morgan fingerprint for a molecule.

    :param mol_data: A molecule (i.e., either a SMILES or an RDKit molecule).
    :param radius: Morgan fingerprint radius.
    :param num_bits: Number of bits in Morgan fingerprint.
    :return: A 1D numpy array containing the counts-based Morgan fingerprint.
    """
    if type(mol_data) == list:
        features = []
        for datapoint in mol_data:
            entry_features = []
            for molecule in datapoint:
                molecule = Chem.MolFromSmiles(molecule) if type(molecule) == str else molecule
                features_vec = AllChem.GetHashedMorganFingerprint(molecule, radius, nBits=num_bits)
                f = np.zeros((1,))
                DataStructs.ConvertToNumpyArray(features_vec, f)
                entry_features.append(f)
            features.extend(entry_features)
        features = np.array(features)
    else:
        mol_data = Chem.MolFromSmiles(mol_data) if type(mol_data) == str else mol_data
        features_vec = AllChem.GetHashedMorganFingerprint(mol_data, radius, nBits=num_bits)
        features = np.zeros((1,))
        DataStructs.ConvertToNumpyArray(features_vec, features)

    return features


try:
    from descriptastorus.descriptors import rdDescriptors, rdNormalizedDescriptors


    @register_features_generator('rdkit_2d')
    def rdkit_2d_features_generator(mol_data: Union[Molecule, List[Molecule]]) -> np.ndarray:
        """
        Generates RDKit 2D features for a molecule.
        :param mol_data: A molecule (i.e., either a SMILES or an RDKit molecule).
        :return: A 1D numpy array containing the RDKit 2D features.
        """
        generator = rdDescriptors.RDKit2D()

        if type(mol_data) == list:
            features = []
            for datapoint in mol_data:
                entry_features = []
                for molecule in datapoint:
                    molecule = Chem.MolToSmiles(molecule, isomericSmiles=True) if type(molecule) != str else molecule
                    f = generator.process(molecule)[1:]
                    entry_features.append(f)
                features.extend(entry_features)
            features = np.array(features)
        else:
            smiles = Chem.MolToSmiles(mol_data, isomericSmiles=True) if type(mol_data) != str else mol_data
            features = np.array(generator.process(smiles)[1:])

        return features

    @register_features_generator('rdkit_2d_normalized')
    def rdkit_2d_normalized_features_generator(mol_data: Union[Molecule, List[Molecule]]) -> np.ndarray:
        """
        Generates RDKit 2D normalized features for a molecule.

        :param mol_data: A molecule (i.e., either a SMILES or an RDKit molecule).
        :return: A 1D numpy array containing the RDKit 2D normalized features.
        """
        generator = rdNormalizedDescriptors.RDKit2DNormalized()

        if type(mol_data) == list:
            features = []
            for datapoint in mol_data:
                entry_features = []
                for molecule in datapoint:
                    molecule = Chem.MolToSmiles(molecule, isomericSmiles=True) if type(molecule) != str else molecule
                    f = generator.process(molecule)[1:]
                    entry_features.append(f)
                features.extend(entry_features)
            features = np.array(features)
        else:
            smiles = Chem.MolToSmiles(mol_data, isomericSmiles=True) if type(mol_data) != str else mol_data
            features = np.array(generator.process(smiles)[1:])

        return features
except ImportError:
    @register_features_generator('rdkit_2d')
    def rdkit_2d_features_generator(mol_data: Union[Molecule, List[Molecule]]) -> np.ndarray:
        """Mock implementation raising an ImportError if descriptastorus cannot be imported."""
        raise ImportError('Failed to import descriptastorus. Please install descriptastorus '
                          '(https://github.com/bp-kelley/descriptastorus) to use RDKit 2D features.')

    @register_features_generator('rdkit_2d_normalized')
    def rdkit_2d_normalized_features_generator(mol_data: Union[Molecule, List[Molecule]]) -> np.ndarray:
        """Mock implementation raising an ImportError if descriptastorus cannot be imported."""
        raise ImportError('Failed to import descriptastorus. Please install descriptastorus '
                          '(https://github.com/bp-kelley/descriptastorus) to use RDKit 2D normalized features.')


"""
Custom features generator template.

Note: The name you use to register the features generator is the name
you will specify on the command line when using the --features_generator <name> flag.
Ex. python train.py ... --features_generator custom ...

@register_features_generator('custom')
def custom_features_generator(mol_data: Union[Molecule, List[Molecule]]) -> np.ndarray:
    if type(mol_data) == list:
        # If your generator supports an input of a list of molecules, implement  
    
    # If you want to use the SMILES string
    smiles = Chem.MolToSmiles(mol, isomericSmiles=True) if type(mol) != str else mol

    # If you want to use the RDKit molecule
    mol = Chem.MolFromSmiles(mol) if type(mol) == str else mol

    # Replace this with code which generates features from the molecule
    features = np.array([0, 0, 1])

    return features
"""
