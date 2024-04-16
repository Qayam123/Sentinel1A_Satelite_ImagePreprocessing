# Need to configure Python to use the SNAP-Python (snappy) interface(https://senbox.atlassian.net/wiki/spaces/SNAP/pages/50855941/Configure+Python+to+use+the+SNAP-Python+snappy+interface)
# Read in unzipped Sentinel-1 GRD products (EW and IW modes)

import os
import gc
import snappy
from snappy import ProductIO, GPF
from snappy import HashMap

# Load SNAP operators
GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()

path = "Folder path in which the unzipped directory of Sentinel 1A Images are kept"
for folder in os.listdir(path):
    gc.enable()
    output = path + folder + "/"
    timestamp = folder.split("_")[4] 
    date = timestamp[:8]
    sentinel_1 = ProductIO.readProduct(output + "/manifest.safe")    
    print(sentinel_1)
    pols = ['VH', 'VV']
    for p in pols:
        polarization = p    

        # Calibration
        parameters = HashMap()
        parameters.put('outputSigmaBand', True)
        parameters.put('sourceBands', 'Intensity_' + polarization)
        parameters.put('selectedPolarisations', polarization)
        parameters.put('outputImageScaleInDb', False)

        calib = output + date + "_calibrate_" + polarization
        target_0 = GPF.createProduct("Calibration", parameters, sentinel_1)
        ProductIO.writeProduct(target_0, calib, 'BEAM-DIMAP')

        # Speckle Filtering
        parameters = HashMap()
        parameters.put('filter', 'Lee')
        parameters.put('filterSizeX', 5)
        parameters.put('filterSizeY', 5)

        speckle_filtered = output + date + "_speckle_filtered_" + polarization
        target_1 = GPF.createProduct("Speckle-Filter", parameters, target_0)
        ProductIO.writeProduct(target_1, speckle_filtered, 'BEAM-DIMAP')

        # Thermal Noise Removal
        parameters = HashMap()
        parameters.put('removeThermalNoise', True)

        thermal_removed = output + date + "_thermal_removed_" + polarization
        target_2 = GPF.createProduct("ThermalNoiseRemoval", parameters, target_1)
        ProductIO.writeProduct(target_2, thermal_removed, 'BEAM-DIMAP')

        # Convert thermal_removed string to product object
        thermal_removed_product = ProductIO.readProduct(thermal_removed + ".dim")

        # Subset
        WKTReader = snappy.jpy.get_type('org.locationtech.jts.io.WKTReader')
	#put lat lon in ddd format
        wkt = "POLYGON(( lat1 lon1, lat2 lon2, lat3 lon3, lat4 lon4, lat1 lon1))"
        geom = WKTReader().read(wkt)
        parameters = HashMap()
        parameters.put('geoRegion', geom)
        parameters.put('outputImageScaleInDb', False)

        subset = output + date + "_subset_" + polarization
        target_3 = GPF.createProduct("Subset", parameters, thermal_removed_product)
        ProductIO.writeProduct(target_3, subset, 'BEAM-DIMAP')

        # Terrain Correction
        parameters = HashMap()
        parameters.put('demResamplingMethod', 'NEAREST_NEIGHBOUR')
        parameters.put('imgResamplingMethod', 'NEAREST_NEIGHBOUR')
        parameters.put('demName', 'SRTM 3Sec')
        parameters.put('pixelSpacingInMeter', 10.0)
        parameters.put('sourceBands', 'Sigma0_' + polarization)

        terrain = output + date + "_corrected_" + polarization
        target_4 = GPF.createProduct("Terrain-Correction", parameters, target_3)
        ProductIO.writeProduct(target_4, terrain, 'GeoTIFF')

