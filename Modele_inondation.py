"""
Model exported as python.
Name : Modèle
Group : 
With QGIS : 33411
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class Modele_inondation(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('bd_topo', 'BD_topo', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('buffer_terre', 'Buffer_terre', type=QgsProcessingParameterNumber.Integer, minValue=0, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('couche_decoupe', 'couche_decoupe', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('hauteur_submersion', 'hauteur_submersion', type=QgsProcessingParameterNumber.Integer, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('hydro', 'hydro', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('mnt', 'MNT', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('ocs', 'OCS', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('population', 'Population', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Mnt_final', 'MNT_final', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Pop_final', 'pop_final', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Bati_final', 'Bati_final', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Ocs_final', 'ocs_final', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(16, model_feedback)
        results = {}
        outputs = {}

        # Cuttt_ocs
        alg_params = {
            'INPUT': parameters['ocs'],
            'OVERLAY': parameters['couche_decoupe'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Cuttt_ocs'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # MNT_cut
        alg_params = {
            'ALPHA_BAND': True,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,  # Utiliser le type de donnée de la couche en entrée
            'EXTRA': '',
            'INPUT': parameters['mnt'],
            'KEEP_RESOLUTION': False,
            'MASK': parameters['couche_decoupe'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'SET_RESOLUTION': False,
            'SOURCE_CRS': 'ProjectCrs',
            'TARGET_CRS': 'ProjectCrs',
            'TARGET_EXTENT': '636236.229800000,651294.631200000,7065147.250000000,7072721.002100000 [EPSG:2154]',
            'X_RESOLUTION': None,
            'Y_RESOLUTION': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Mnt_cut'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Cut_batii
        alg_params = {
            'INPUT': parameters['bd_topo'],
            'OVERLAY': parameters['couche_decoupe'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Cut_batii'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Cut_pooop
        alg_params = {
            'INPUT': parameters['population'],
            'OVERLAY': parameters['couche_decoupe'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Cut_pooop'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # cut_hydrooo
        alg_params = {
            'INPUT': parameters['hydro'],
            'OVERLAY': parameters['couche_decoupe'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Cut_hydrooo'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Bati_alt
        alg_params = {
            'COLUMN_PREFIX': '_',
            'INPUT': outputs['Cut_batii']['OUTPUT'],
            'INPUT_RASTER': outputs['Mnt_cut']['OUTPUT'],
            'RASTER_BAND': 1,
            'STATISTICS': [3],  # Médiane
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Bati_alt'] = processing.run('native:zonalstatisticsfb', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # OCS_alt
        alg_params = {
            'COLUMN_PREFIX': '_',
            'INPUT': outputs['Cuttt_ocs']['OUTPUT'],
            'INPUT_RASTER': outputs['Mnt_cut']['OUTPUT'],
            'RASTER_BAND': 1,
            'STATISTICS': [3,5],  # Médiane,Minimum
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Ocs_alt'] = processing.run('native:zonalstatisticsfb', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # pop_alt
        alg_params = {
            'COLUMN_PREFIX': '_',
            'INPUT': outputs['Cut_pooop']['OUTPUT'],
            'INPUT_RASTER': outputs['Mnt_cut']['OUTPUT'],
            'RASTER_BAND': 1,
            'STATISTICS': [3],  # Médiane
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Pop_alt'] = processing.run('native:zonalstatisticsfb', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Buffer_hydro
        alg_params = {
            'DISSOLVE': True,
            'DISTANCE': parameters['buffer_terre'],
            'END_CAP_STYLE': 0,  # Rond
            'INPUT': outputs['Cut_hydrooo']['OUTPUT'],
            'JOIN_STYLE': 0,  # Rond
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'SEPARATE_DISJOINT': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer_hydro'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Extraire_pop_inf5
        alg_params = {
            'FIELD': '_median',
            'INPUT': outputs['Pop_alt']['OUTPUT'],
            'OPERATOR': 4,  # <
            'VALUE': parameters['hauteur_submersion'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Extraire_pop_inf5'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Extraire_bati_inf5
        alg_params = {
            'FIELD': '_median',
            'INPUT': outputs['Bati_alt']['OUTPUT'],
            'OPERATOR': 4,  # <
            'VALUE': parameters['hauteur_submersion'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Extraire_bati_inf5'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Extraire_OCS_inf5
        alg_params = {
            'FIELD': '_min',
            'INPUT': outputs['Ocs_alt']['OUTPUT'],
            'OPERATOR': 4,  # <
            'VALUE': parameters['hauteur_submersion'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Extraire_ocs_inf5'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Inter_OCS_hydro
        alg_params = {
            'GRID_SIZE': None,
            'INPUT': outputs['Extraire_ocs_inf5']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'OVERLAY': outputs['Buffer_hydro']['OUTPUT'],
            'OVERLAY_FIELDS': [''],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': parameters['Ocs_final']
        }
        outputs['Inter_ocs_hydro'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Ocs_final'] = outputs['Inter_ocs_hydro']['OUTPUT']

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # MNT_cut_finale
        alg_params = {
            'ALPHA_BAND': True,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,  # Utiliser le type de donnée de la couche en entrée
            'EXTRA': '',
            'INPUT': parameters['mnt'],
            'KEEP_RESOLUTION': False,
            'MASK': outputs['Buffer_hydro']['OUTPUT'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'SET_RESOLUTION': False,
            'SOURCE_CRS': 'ProjectCrs',
            'TARGET_CRS': 'ProjectCrs',
            'TARGET_EXTENT': None,
            'X_RESOLUTION': None,
            'Y_RESOLUTION': None,
            'OUTPUT': parameters['Mnt_final']
        }
        outputs['Mnt_cut_finale'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Mnt_final'] = outputs['Mnt_cut_finale']['OUTPUT']

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Extraire_Pop_hydro
        alg_params = {
            'INPUT': outputs['Extraire_pop_inf5']['OUTPUT'],
            'INTERSECT': outputs['Buffer_hydro']['OUTPUT'],
            'PREDICATE': [0],  # intersecte
            'OUTPUT': parameters['Pop_final']
        }
        outputs['Extraire_pop_hydro'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Pop_final'] = outputs['Extraire_pop_hydro']['OUTPUT']

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Extraire_Bati_hydro
        alg_params = {
            'INPUT': outputs['Extraire_bati_inf5']['OUTPUT'],
            'INTERSECT': outputs['Buffer_hydro']['OUTPUT'],
            'PREDICATE': [0],  # intersecte
            'OUTPUT': parameters['Bati_final']
        }
        outputs['Extraire_bati_hydro'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Bati_final'] = outputs['Extraire_bati_hydro']['OUTPUT']
        return results

    def name(self):
        return 'Modèle'

    def displayName(self):
        return 'Modèle'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Modle()
