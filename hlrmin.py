# originally the fwhm was 0.65 but i varying it with 5 variables ranging from 0 to 1. I then plotted it against time to see how it affected the combination of 1 psf with that of 5 galaxy profiles.
import matplotlib.pyplot as plt
import sys
import os
import math
import numpy
import logging
import time
import galsim
import numpy as np
from scipy.interpolate import *

def func(file_name, random_seed, pixel_scale, nx, ny, sky_level, gal_flux_min, gal_flux_max, gal_hlr_min, gal_hlr_max, gal_e_min, gal_e_max, psf_fwhm, gsparams, folding_threshold, maxk_threshold, xvalue_accuracy, kvalue_accuracy, shoot_accuracy, minimum_fft_size, psf1, psf2, psf3_inner, psf3_outer, psf3, atmos, aberrations, psf4, optics,  psf5, psfs, psf_names, psf_times, psf_fft_times, psf_phot_times, gal1, gal2, gal3, gal4, bulge, disk, gal5, gals, gal_names, gal_times, gal_fft_times, gal_phot_times, setup_times, fft_times, phot_times, noise_times, k, all_fluxes, psf, psf_name, gal, gal_name, rng, flux, y, this_gal, hlr, beta_ellip, ellip, gal_shape, final, fft_image, phot_image, sky_level_pixel, pd):
    def main(argv):
        
          logging.basicConfig(format="%(message)s", level=logging.INFO, stream=sys.stdout)
          logger = logging.getLogger("demo7")
          
          ### Make output directory if not already present.
          if not os.path.isdir('output'):
              os.mkdir('output')
          
          file_name = os.path.join('output','cube_phot.fits.gz')


          scaleimg_y=[]
          scaleimg_x_DFT=[]
          scaleimg_x_Photon=[]
          hlrmin_range = np.linspace(-3,3,5)
          for num in hlrmin_range:
              

              ### Define some parameters we'll use below.
              random_seed = 553728
              pixel_scale =.28      # arcsec*
              nx = 64
              ny = 64
              sky_level = 1.e4
              gal_flux_min = 1.e1     # Range for galaxy flux
              gal_flux_max = 1.e5
              gal_hlr_min = num       # arcsec
              gal_hlr_max = 1.3      # arcsec
              gal_e_min = 0.          # Range for ellipticity
              gal_e_max = 0.8
              
              psf_fwhm = 0.65         # arcsec
              
              # We encapsulate these parameters with an object called GSParams.  The default values
              # are intended to be accurate enough for normal precision shear tests, without sacrificing
              # too much speed.Any PSF or galaxy object can be given a gsparams argument on construction that can
              # have different values to make the calculation more or less accurate (typically trading
              # off for speed or memory).
              
              gsparams = galsim.GSParams(
                 folding_threshold=1.e-2, # maximum fractional flux that may be folded around edge of FFT
                 maxk_threshold=2.e-3,    # k-values less than this may be excluded off edge of FFT
                 xvalue_accuracy=1.e-4,   # approximations in real space aim to be this accurate
                 kvalue_accuracy=1.e-4,   # approximations in fourier space aim to be this accurate
                 shoot_accuracy=1.e-4,    # approximations in photon shooting aim to be this accurate
                 minimum_fft_size=64)     # minimum size of ffts

              logger.info('Starting psf')
                 
              # Make the PSF profiles:
              ### psf 1
              psf1 = galsim.Gaussian(fwhm = psf_fwhm, gsparams=gsparams)
             
              ### psf 2
              psf2 = galsim.Moffat(fwhm = psf_fwhm, beta = 2.4, gsparams=gsparams)
             
              ### psf 3
              psf3_inner = galsim.Gaussian(fwhm = psf_fwhm, flux = 0.8, gsparams=gsparams)
              psf3_outer = galsim.Gaussian(fwhm = 2*psf_fwhm, flux = 0.2, gsparams=gsparams)
              psf3 = psf3_inner + psf3_outer
              atmos = galsim.Gaussian(fwhm = psf_fwhm, gsparams=gsparams)
             
              ### defining the telescope
             
              # The OpticalPSF and set of Zernike values chosen below correspond to a reasonably well aligned,
              # smallish ~0.3m / 12 inch diameter telescope with a central obscuration of ~0.12m or 5 inches
              # diameter, being used in optical wavebands.
             
              aberrations = [ 0.0 ] * 12          # Set the initial size.
              aberrations[4] = 0.06               # Noll index 4 = Defocus
              aberrations[5:7] = [ 0.12, -0.08 ]  # Noll index 5,6 = Astigmatism
              aberrations[7:9] = [ 0.07, 0.04 ]   # Noll index 7,8 = Coma
              aberrations[11] = -0.13             # Noll index 11 = Spherical
                 
              optics = galsim.OpticalPSF(
                                            lam_over_diam = 0.6 * psf_fwhm, obscuration = 0.4, aberrations = aberrations,
                                            gsparams=gsparams)
                 
              ### psf 4
              psf4 = galsim.Convolve([atmos, optics]) # Convolve inherits the gsparams from the first
              # item in the list.  (Or you can supply a gsparams
              # argument explicitly if you want to override this.)
              atmos = galsim.Kolmogorov(fwhm = psf_fwhm, gsparams=gsparams)
              optics = galsim.Airy(lam_over_diam = 0.3 * psf_fwhm, gsparams=gsparams)

              ### psf 5
              psf5 = galsim.Convolve([atmos,optics])

              ### define where to keep the psfs info
              psfs = [psf1, psf2, psf3, psf4, psf5]
              psf_names = ["Gaussian", "Moffat", "Double Gaussian", "OpticalPSF", "Kolmogorov * Airy"]
              psf_times = [0,0,0,0,0]
              psf_fft_times = [0,0,0,0,0]
              psf_phot_times = [0,0,0,0,0]

              # Make the galaxy profiles:

              ### gal 1
              gal1 = galsim.Gaussian(half_light_radius = 1, gsparams=gsparams)

              ### gal 2
              gal2 = galsim.Exponential(half_light_radius = 1, gsparams=gsparams)

              ### gal 3
              gal3 = galsim.DeVaucouleurs(half_light_radius = 1, gsparams=gsparams)

              ### gal 4
              gal4 = galsim.Sersic(half_light_radius = 1, n = 2.5, gsparams=gsparams)
              bulge = galsim.Sersic(half_light_radius = 0.7, n = 3.2, trunc = 8.5, gsparams=gsparams)
              disk = galsim.Sersic(half_light_radius = 1.2, n = 1.5, gsparams=gsparams)

              ### gal 5
              gal5 = 0.4*bulge + 0.6*disk  # Net half-light radius is only approximate for this one.

              ### define where to keep the galaxys info
              gals = [gal1, gal2, gal3, gal4, gal5]
              gal_names = ["Gaussian", "Exponential", "Devaucouleurs", "n=2.5 Sersic", "Bulge + Disk"]
              gal_times = [0,0,0,0,0]
              gal_fft_times = [0,0,0,0,0]
              gal_phot_times = [0,0,0,0,0]

              ### initial time conditions
              # Other times to keep track of:
              setup_times = 0
              fft_times = 0
              phot_times = 0
              noise_times = 0

              # Loop over combinations of psf, gal, and make 4 random choices for flux, size, shape.
              all_images = []
              k = 0

              n=[]
              x_DFT=[]
              x_Photon=[]
              y=[]
              all_fluxes = np.linspace(gal_flux_min,gal_flux_max,100)

              ### will loop through the numbers (amount) of psfs
              for ipsf in range(len(psfs)):
              
                 ### calls on the 5 psfs and their names
                 psf = psfs[ipsf]
                 psf_name = psf_names[ipsf]
                         
                 ### outputs the psf number and the psf information needed to create an object
                 logger.info('psf %d: %s',ipsf+1,psf)
                             
                 logger.debug('repr = %r',psf)
                 
                 ### will loop through the numbers (amount) of galaxies
                 for igal in range(len(gals)):
                     
                         ### calls on the 5 galaxies and their names
                         gal = gals[igal]
                         gal_name = gal_names[igal]
                             
                         ### outputs the psf number and the psf information needed to create an object
                         logger.info('   galaxy %d: %s',igal+1,gal)
                         logger.debug('   repr = %r',gal)
                         
                         ### will loop though 0,1,2,3 flux, size, and shape to create 4 images for each
                         ### combination of galaxy and psf
                         for i in range(4):
                             logger.debug('      Start work on image %d',i)
                             #---> start here

                             ### this willl return the time in seconds
                             t1 = time.time()
                                 
                             ### generate randomly a number
                             # Initialize the random number generator we will be using.
                             rng = galsim.UniformDeviate(random_seed+k+1)
                                 
                             ### use the random numbers for the flux
                             # Generate random variates:
                             flux = all_fluxes[i]
                             y = np.append(y,flux)
                                 
                             # Use a new variable name, since we'll want to keep the original unmodified.
                             this_gal = gal.withFlux(flux)
                                                                                     
                             ### use the random numbers for the hlr
                             hlr = rng() * (gal_hlr_max-gal_hlr_min) + gal_hlr_min
                                                                                         
                             # Use a new variable name, since we'll want to keep the original unmodified.
                             this_gal = this_gal.dilate(hlr)
                                                                                             
                             ### use the random numbers for the ellipticity
                             beta_ellip = rng() * 2*math.pi * galsim.radians
                             ellip = rng() * (gal_e_max-gal_e_min) + gal_e_min
                             gal_shape = galsim.Shear(e=ellip, beta=beta_ellip)
                                                                                                         
                             # Use a new variable name, since we'll want to keep the original unmodified.
                             this_gal = this_gal.shear(gal_shape)
                                 
                             ### build the final object by combinging the galaxy and psf
                             final = galsim.Convolve([this_gal, psf])
                                     
                             ### create the images and save them in an empty array
                             image = galsim.ImageF(2*nx+2, ny, scale=pixel_scale)
                                 
                             ### make a views subset of the larger image
                             fft_image = image[galsim.BoundsI(1, nx, 1, ny)]
                             phot_image = image[galsim.BoundsI(nx+3, 2*nx+2, 1, ny)]
                                                                                                                             
                             logger.debug('      Read in training sample galaxy and PSF from file')
                                 
                             ### record time
                             
                             t2 = time.time()
                              
                             ### Draw the profile explicity through fft for the convolution
                             final.drawImage(fft_image, method='fft')
                                 
                             logger.debug('      Drew fft image.  Total drawn flux = %f.  .flux = %f',
                                          fft_image.array.sum(),final.getFlux())
                             ### record time
                             t3 = time.time()
                                 
                             ### Add Poisson noise to the fft image convolution
                             sky_level_pixel = sky_level * pixel_scale**2
                             fft_image.addNoise(galsim.PoissonNoise(rng, sky_level=sky_level_pixel))
                             ### record time
                             t4 = time.time()
                                 
                             # The next two lines are just to get the output from this demo script
                             # to match the output from the parsing of demo7.yaml.
                             rng = galsim.UniformDeviate(random_seed+k+1)
                             rng(); rng(); rng(); rng();
                                 
                             ### repeat for photon-shooting
                             final.drawImage(phot_image, method='phot', max_extra_noise=sky_level_pixel/100,
                                             rng=rng)
                                 
                             ### record time
                             t5 = time.time()
                                 
                             ### For photon shooting, galaxy already has Poisson noise, so we want to make sure not to add that noise again.
                             ### Thus, we just add sky noise, which is Poisson with the mean = sky_level_pixel
                             pd = galsim.PoissonDeviate(rng, mean=sky_level_pixel)
                                 
                             # DeviateNoise just adds the action of the given deviate to every pixel.
                             phot_image.addNoise(galsim.DeviateNoise(pd))
                                 
                             # For PoissonDeviate, the mean is not zero, so for a background-subtracted
                             # image, we need to subtract the mean back off when we are done.
                             phot_image -= sky_level_pixel
                                 
                             logger.debug('      Added Poisson noise.  Image fluxes are now %f and %f',
                                          fft_image.array.sum(), phot_image.array.sum())
                                 
                             ### record time
                             t6 = time.time()
                             #<----end here (return stuff)
                             image, t1, t2, t3, t4, t5, t6, k, flux, hlr, gal_shape, y, x_DFT, x_Photon, psfs, gals, file_name = func(file_name, random_seed, pixel_scale, nx, ny, sky_level, gal_flux_min, gal_flux_max, gal_hlr_min, gal_hlr_max, gal_e_min, gal_e_max, psf_fwhm, gsparams, folding_threshold, maxk_threshold, xvalue_accuracy, kvalue_accuracy, shoot_accuracy, minimum_fft_size, psf1, psf2, psf3_inner, psf3_outer, psf3, atmos, aberrations, psf4, optics,  psf5, psfs, psf_names, psf_times, psf_fft_times, psf_phot_times, gal1, gal2, gal3, gal4, bulge, disk, gal5, gals, gal_names, gal_times, gal_fft_times, gal_phot_times, setup_times, fft_times, phot_times, noise_times, k, all_fluxes, psf, psf_name, gal, gal_name, rng, flux, y, this_gal, hlr, beta_ellip, ellip, gal_shape, final, fft_image, phot_image, sky_level_pixel, pd)


                             ### Store that into the list of all images
                             all_images += [image]
                                 
                             ### add an itteration though the loop for the psf and galaxy combination images
                             k = k+1
                                 
                             ### express the flux,hlr, and ellip of each image combination,4 for every loop
                             logger.info('      %d: flux = %.2e, hlr = %.2f, ellip = (%.2f,%.2f)',
                                         k, flux, hlr, gal_shape.getE1(), gal_shape.getE2())
                                 
                                                                                                                                                                                                             
                             logger.debug('      Times: %f, %f, %f, %f, %f',t2-t1, t3-t2, t4-t3, t5-t4, t6-t5)
                             
                             psf_times[ipsf] += t6-t1
                             psf_fft_times[ipsf] += t3-t2
                             psf_phot_times[ipsf] += t5-t4
                             gal_times[igal] += t6-t1
                             gal_fft_times[igal] += t3-t2
                             gal_phot_times[igal] += t5-t4
                             setup_times += t2-t1
                             fft_times += t3-t2
                             phot_times += t5-t4
                             noise_times += t4-t3 + t6-t5
                             x_DFT = np.append(x_DFT,gal_fft_times[igal])
                             x_Photon = np.append(x_Photon,gal_phot_times[igal])
                                 
                             #### flux and time of each galaxy profile with each PSF
              scaleimg_y=np.append(scaleimg_y,y)
              scaleimg_x_DFT=np.append(scaleimg_x_DFT,x_DFT)
              scaleimg_x_Photon=np.append(scaleimg_x_Photon,x_Photon)

          logger.info('Done making images of galaxies')

        #### the DFT time for the first 5 galaxies for the first psf and the 5 pixels

          x1_DFT_1=(scaleimg_x_DFT[0],scaleimg_x_DFT[100],scaleimg_x_DFT[200],scaleimg_x_DFT[300],scaleimg_x_DFT[400])
          x1_DFT_2=(scaleimg_x_DFT[1],scaleimg_x_DFT[101],scaleimg_x_DFT[201],scaleimg_x_DFT[301],scaleimg_x_DFT[401])
          x1_DFT_3=(scaleimg_x_DFT[2],scaleimg_x_DFT[102],scaleimg_x_DFT[202],scaleimg_x_DFT[302],scaleimg_x_DFT[402])
          x1_DFT_4=(scaleimg_x_DFT[3],scaleimg_x_DFT[103],scaleimg_x_DFT[203],scaleimg_x_DFT[303],scaleimg_x_DFT[403])
          x1_DFT_5=(scaleimg_x_DFT[4],scaleimg_x_DFT[104],scaleimg_x_DFT[204],scaleimg_x_DFT[304],scaleimg_x_DFT[404])


        #### the Photon-shooting time for the first 5 galaxies for the first psf and the 5 pixels

          x1_Photon_1=(scaleimg_x_Photon[0],scaleimg_x_Photon[100],scaleimg_x_Photon[200],scaleimg_x_Photon[300],scaleimg_x_Photon[400])
          x1_Photon_2=(scaleimg_x_Photon[1],scaleimg_x_Photon[101],scaleimg_x_Photon[201],scaleimg_x_Photon[301],scaleimg_x_Photon[401])
          x1_Photon_3=(scaleimg_x_Photon[2],scaleimg_x_Photon[102],scaleimg_x_Photon[202],scaleimg_x_Photon[302],scaleimg_x_Photon[402])
          x1_Photon_4=(scaleimg_x_Photon[3],scaleimg_x_Photon[103],scaleimg_x_Photon[203],scaleimg_x_Photon[303],scaleimg_x_Photon[403])
          x1_Photon_5=(scaleimg_x_Photon[4],scaleimg_x_Photon[104],scaleimg_x_Photon[204],scaleimg_x_Photon[304],scaleimg_x_Photon[404],)

        ###subtraction of points

          xnew_1=[]
          xnew_2=[]
          xnew_3=[]
          xnew_4=[]
          xnew_5=[]
          for a,b,c,d,e,f,g,h,i,j in zip (x1_DFT_1,x1_Photon_1,x1_DFT_2,x1_Photon_2,x1_DFT_3,x1_Photon_3,x1_DFT_4,x1_Photon_4,x1_DFT_5,x1_Photon_5):
              x1=a-b
              x2=c-d
              x3=e-f
              x4=g-h
              x5=i-j
              xnew_1= np.append(xnew_1,x1)
              xnew_2= np.append(xnew_2,x2)
              xnew_3= np.append(xnew_3,x3)
              xnew_4= np.append(xnew_4,x4)
              xnew_5= np.append(xnew_5,x5)

          y = [0,0,0,0,0]

          f, (ax1, ax2) = plt.subplots(2, sharex=True, sharey=True)
          l1, = ax1.plot(hlrmin_range,x1_DFT_1, 'b-')
          l2, = ax1.plot(hlrmin_range,x1_Photon_1, 'g-')
          l3, = ax1.plot(hlrmin_range,y,'r--')
          ax1.set_title('Gaussian PSF with Gaussian Galaxy Profile at flux=10')
          l4, = ax2.plot(hlrmin_range,xnew_1,'y-')
          l5, = ax2.plot(hlrmin_range,y,'r--')
          plt.legend([l1,l2,l3,l4,l5],['DFT','Photon','Y=0','DFT - Photon','Y=0'], loc='upper right')
          plt.xlabel('hlrmin')
          plt.ylabel('time')
          f.subplots_adjust(hspace=0)
          plt.setp([a.get_xticklabels() for a in f.axes[:-1]], visible=False)
          plt.savefig('hlrmin_1.png')

          f, (ax1, ax2) = plt.subplots(2, sharex=True, sharey=True)
          l1, = ax1.plot(hlrmin_range,x1_DFT_2, 'b-')
          l2, = ax1.plot(hlrmin_range,x1_Photon_2, 'g-')
          l3, = ax1.plot(hlrmin_range,y,'r--')
          ax1.set_title('Gaussian PSF with Exponential Galaxy Profile at flux=')
          l4, = ax2.plot(hlrmin_range,xnew_2,'y-')
          l5, = ax2.plot(hlrmin_range,y,'r--')
          plt.legend([l1,l2,l3,l4,l5],['DFT','Photon','Y=0','DFT - Photon','Y=0'], loc='upper right')
          plt.xlabel('hlrmin')
          plt.ylabel('time')
          plt.legend(loc='best')
          f.subplots_adjust(hspace=0)
          plt.setp([a.get_xticklabels() for a in f.axes[:-1]], visible=False)
          plt.savefig('hlrmin_2.png')

          f, (ax1, ax2) = plt.subplots(2, sharex=True, sharey=True)
          l1, = ax1.plot(hlrmin_range,x1_DFT_3, 'b-')
          l2, = ax1.plot(hlrmin_range,x1_Photon_3, 'g-')
          l3, = ax1.plot(hlrmin_range,y,'r--')
          ax1.set_title('Gaussian PSF with Devaucouleurs Galaxy Profile at flux=')
          l4, = ax2.plot(hlrmin_range,xnew_3, 'y-')
          l5, = ax2.plot(hlrmin_range,y,'r--')
          plt.legend([l1,l2,l3,l4,l5],['DFT','Photon','Y=0','DFT - Photon','Y=0'], loc='upper right')
          plt.xlabel('hlrmin')
          plt.ylabel('time')
          plt.legend(loc='best')
          f.subplots_adjust(hspace=0)
          plt.setp([a.get_xticklabels() for a in f.axes[:-1]], visible=False)
          plt.savefig('hlrmin_3.png')

          f, (ax1, ax2) = plt.subplots(2, sharex=True, sharey=True)
          l1, = ax1.plot(hlrmin_range,x1_DFT_4, 'b-')
          l2, = ax1.plot(hlrmin_range,x1_Photon_4, 'g-')
          l3, = ax1.plot(hlrmin_range,y,'r--')
          ax1.set_title('Gaussian PSF with n=2.5 Sersic Galaxy Profile at flux=')
          l4, = ax2.plot(hlrmin_range,xnew_4, 'y-')
          l5, = ax2.plot(hlrmin_range,y,'r--')
          plt.legend([l1,l2,l3,l4,l5],['DFT','Photon','Y=0','DFT - Photon','Y=0'], loc='upper right')
          plt.xlabel('hlrmin')
          plt.ylabel('time')
          plt.legend(loc='best')
          f.subplots_adjust(hspace=0)
          plt.setp([a.get_xticklabels() for a in f.axes[:-1]], visible=False)
          plt.savefig('hlrmin_4.png')

          f, (ax1, ax2) = plt.subplots(2, sharex=True, sharey=True)
          l1, = ax1.plot(hlrmin_range,x1_DFT_5, 'b-')
          l2, = ax1.plot(hlrmin_range,x1_Photon_5, 'g-')
          l3, = ax1.plot(hlrmin_range,y,'r--')
          ax1.set_title('Gaussian PSF with Bulge + Disk Galaxy Profile at flux=')
          l4, = ax2.plot(hlrmin_range,xnew_5, 'y-')
          l5, = ax2.plot(hlrmin_range,y,'r--')
          plt.legend([l1,l2,l3,l4,l5],['DFT','Photon','Y=0','DFT - Photon','Y=0'], loc='upper right')
          plt.xlabel('hlrmin')
          plt.ylabel('time')
          plt.legend(loc='best')
          f.subplots_adjust(hspace=0)
          plt.setp([a.get_xticklabels() for a in f.axes[:-1]], visible=False)
          plt.savefig('hlrmin_5.png')


          plt.show()

        ### breakdown of psf and galaxy types as well as overal timing statistics
          logger.info('')
          logger.info('Some timing statistics:')
          logger.info('   Total time for setup steps = %f',setup_times)
          logger.info('   Total time for regular fft drawing = %f',fft_times)
          logger.info('   Total time for photon shooting = %f',phot_times)
          logger.info('   Total time for adding noise = %f',noise_times)
          logger.info('')
          logger.info('Breakdown by PSF type:')
          for ipsf in range(len(psfs)):
              logger.info('   %s: Total time = %f  (fft: %f, phot: %f)',
                          psf_names[ipsf],psf_times[ipsf],psf_fft_times[ipsf],psf_phot_times[ipsf])
          logger.info('')
          logger.info('Breakdown by Galaxy type:')
          for igal in range(len(gals)):
              logger.info('   %s: Total time = %f  (fft: %f, phot: %f)',
                          gal_names[igal],gal_times[igal],gal_fft_times[igal],gal_phot_times[igal])
          logger.info('')
          
        ### compress into a gzip file and save a a cube
          galsim.fits.writeCube(all_images, file_name, compression='gzip')
          logger.info('Wrote fft image to fits data cube %r',file_name)

    if __name__ == "__main__":
        main(sys.argv)


