#!/usr/bin/env python
"""
Cumulant code that reads GW outputs and 
calculates the cumulant spectra functions.
TODO: mpi4py to run MPI
pyNFFT to realize the non-uniform FFT from 
gt to gw, this will make the convergence
faster.
"""
from __future__ import print_function
import numpy as np;
from multipole import *
import matplotlib.pylab as plt;
from scipy.interpolate import interp1d
import sys
from os.path import isfile, join, isdir
from os import getcwd, pardir, mkdir, chdir

def read_eqp_abinit():
    import numpy as np;
    if isfile("eqp_abinit.dat"):
        print(" Reading file eqp_abinit.dat... ")
        eqpfile = open("eqp_abinit.dat");
        eqp_abinit = [];
        for line in eqpfile.readlines():
            eqp_abinit.append(map(float,line.split()));
        eqpfile.close()
        print("Done.")
        eqp_abinit = np.array(eqp_abinit);
    else:
        print("eqp_abinit.dat not found!")
        sys.exit(1)
    return eqp_abinit

def read_hartree():
    import numpy as np;
    if isfile("hartree.dat"):
        print(" Reading file hartree.dat... ")
        hartreefile = open("hartree.dat");
        hartree = [];
        for line in hartreefile.readlines():
            hartree.append(map(float,line.split()));
        hartreefile.close()
        print("Done.")
        hartree = np.array(hartree);

    elif isfile("E_lda.dat") and isfile("Vxc.dat"):
        print(" Auxiliary file (hartree.dat) not found.")
        print(" Reading files E_lda.dat and Vxc.dat... ")
        Eldafile = open("E_lda.dat");
        Vxcfile = open("Vxc.dat");
        elda = [];
        vxc = [];
        for line in Eldafile.readlines():
            elda.append(map(float,line.split()));
        Eldafile.close()
        for line in Vxcfile.readlines():
            vxc.append(map(float,line.split()));
        Vxcfile.close()
        print("Done.")
        elda = np.array(elda);
        vxc = np.array(vxc);
        hartree = elda - vxc
    else:
        print ("hartree.dat not found! Impossible to continue!!")
        sys.exit(1)
    return hartree
    
def read_lda():
    import numpy as np;
    if isfile("E_lda.dat"):
        print(" Reading file E_lda.dat... ")
        ldafile = open("E_lda.dat");
        Elda = [];
        for line in ldafile.readlines():
            Elda.append(map(float,line.split()));
        ldafile.close()
        print("Done.")
        Elda = np.array(Elda);

    else:
        print ("E_lda.dat not found!")
        sys.exit(1)
    return Elda

def read_wtk():
    import numpy as np;
    if isfile("wtk.dat"):
        wtkfile = open("wtk.dat");    
        wtk = [];
        for line in wtkfile.readlines():
            wtk.append((float(line)));
        wtkfile.close()
        wtk = np.array(wtk); 
    else :
        print("wtk.dat not found!")
        sys.exit(1)
    return wtk

def read_sigfile(sigfilename, nkpt, bdgw_min, bdgw_max, spin=0, nspin=0):
    """
    this function reads _SIG file of abinit GW calculation
    and return the real and imaag part of self-energy for 
    the band range in (bdgw_min, bdgw_max)
    """
    import glob
    from time import sleep
    print("read_sigfile :: ")
    # We put the content of the file (lines) in this array
    #sigfilename = invar_dict['sigmafile']
    #spin = int(invar_dict['spin'])
    #nspin = int(invar_dict['nspin'])
    #en=[] 
    if isfile(sigfilename):
        insigfile = open(sigfilename);
    #elif sigfilename is None:
    else:
        print("File "+ sigfilename+" not found.")
        sigfilename = glob.glob('*_SIG')[0]
        print("Looking automatically for a _SIG file... ",sigfilename)
        insigfile = open(raw_input("Self-energy file name (_SIG): "))
    # We put the content of the file (lines) in this array
    filelines = insigfile.readlines()
    firstbd = 0
    lastbd = 0
    nbd = 0
    #sngl_row = True # are data not split in more than 1 line?
    with open(sigfilename) as insigfile:
        filelines = insigfile.readlines() 
        #nkpt = calc_nkpt_sigfile(insigfile,spin)
        #if invar_dict['gwcode'] == 'exciting':
         #   invar_dict['wtk'] = read_wtk_sigfile(insigfile)
        insigfile.seek(0)
        insigfile.readline()
        line = insigfile.readline()
        #firstbd = int(line.split()[-2])
        #lastbd =  int(line.split()[-1])
        firstbd = bdgw_min
        lastbd = bdgw_max
        nbd = lastbd - firstbd + 1
        print("nbd:",nbd)
        num_cols = len(insigfile.readline().split())
        num_cols2 = len(insigfile.readline().split())
        print("numcols:",num_cols)
        print("numcols2:",num_cols2)
        if num_cols != num_cols2: 
            print()
            print(" WARNING: newlines in _SIG file.")
            print(" Reshaping _SIG file structure...")
            print(" _SIG file length (rows):", len(filelines))
            new_list = []
            nline = 0
            a = []
            b = []
            for line in filelines:
                #if line.split()[0] == "#":
                if '#' in line:
                    print(line.strip('\n'))
                    continue
                elif nline == 0: 
                    a = line.strip('\n')
                    nline += 1
                else: 
                    b = line.strip('\n')
                    new_list.append(a + " " + b)
                    nline = 0
            print("New shape for _SIG array:",np.asarray(new_list).shape)
            tmplist = []
            tmplist2 = []
            for line in new_list:
                tmplist.append(map(float,line.split())[0])
                tmplist2.append(map(float,line.split())[1:])
            for el1 in tmplist2:
                for j in el1:
                    try:
                        float(j)
                    except:
                        print(j)
            #tmplist = map(float,tmplist)
            #tmplist2 = map(float,tmplist2)
            xen = np.asarray(tmplist)
            x = np.asarray(tmplist2)
        else:
            insigfile.seek(0)
            xen = np.genfromtxt(sigfilename,usecols = 0)
            insigfile.seek(0)
            x = np.genfromtxt(sigfilename,usecols = range(1,num_cols), filling_values = 'myNaN')
    #nkpt = int(invar_dict['nkpt'])
    print("nkpt:",nkpt)
    print("spin:",spin)
    print("nspin:",nspin)
    # From a long line to a proper 2D array, then only first row
    #print(xen.shape)
    print("x.shape", x.shape)
    if spin == 1 and nspin == 0:
        nspin = 2
    else:
        nspin = 1
    print("nspin:",nspin)
    print("size(xen):",xen.size)
    print("The size of a single energy array should be",\
            float(np.size(xen))/nkpt/nspin)
    en = xen.reshape(nkpt*nspin,np.size(xen)/nkpt/nspin)[0]
    #en = xen.reshape(nkpt,np.size(xen)/nkpt)[0]
    print("New shape en:",np.shape(en))
    print("First row of x:",x[0])
    #nb_clos = 3
  #  if invar_dict['gwcode'] == 'abinit':
   #     nb_cols = 3
   # elif invar_dict['gwcode'] == 'exciting':
   #     nb_cols = 2
       #b = x.reshape(nkpt*nspin, np.size(x)/nkpt/nspin/nbd/3, 3*nbd)
    b = x.reshape(nkpt*nspin, np.size(x)/nkpt/nspin/nbd/3, 3*nbd)
    print("New shape x:", b.shape)
    y = b[0::nspin,:, 0::3]
    z = b[0::nspin,:, 1::3]
    res = np.rollaxis(y, -1, 1)
    ims = np.rollaxis(z, -1, 1)
    print("New shape res, ims:", res.shape)
    print("First and last band in _SIG file:", firstbd, lastbd)
    print(" Done.")

    return en, res, ims 

def calc_spf_gw(bdrange, kptrange, bdgw_min, wtk, en, enmin, enmax, res,
                ims, hartree, efermi, invar_eta):
    import numpy as np;
    print("calc_spf_gw ::")
    newdx = 0.005
    if enmin < en[0] and enmax >= en[-1]:
        newen = np.arange(en[0],en[-1],newdx)
    elif enmin < en[0]:
        newen = np.arange(en[0],enmax,newdx)
    elif enmax >= en[-1] :
        newen = np.arange(enmin,en[-1],newdx)
    else :
        newen = np.arange(enmin,enmax,newdx)
    print (" ### Interpolation and calculation of A(\omega)_GW...  ")
    spftot = np.zeros((np.size(newen)));
    # Here we interpolate re and im sigma
    # for each band and k point
    for ik in kptrange:
        ikeff = ik + 1
        for ib in bdrange:
            ibeff = ib + bdgw_min
            interpres = interp1d(en, res[ik,ib], kind = 'linear', axis = -1)
            interpims = interp1d(en, ims[ik,ib], kind = 'linear', axis = -1)
            tmpres = interpres(newen)
            redenom = newen - hartree[ik,ib] - interpres(newen)
            tmpim = interpims(newen)
            spfkb = wtk[ik] * abs(tmpim)/np.pi/(redenom**2 + tmpim**2)
            spftot += spfkb
            outnamekb = "spf_gw-k"+str("%02d"%(ikeff))+"-b"+str("%02d"%(ibeff))+".dat"
            outfilekb = open(outnamekb,'w')
            for ien in xrange(np.size(newen)) :
                outfilekb.write("%8.4f %12.8e %12.8e %12.8e %12.8e\n" % (newen[ien], spfkb[ien], redenom[ien], tmpres[ien], tmpim[ien]))
            outfilekb.close()
    return newen, spftot



def find_eqp_resigma(en, resigma, efermi):
    """
    This function is supposed to deal with the plasmaron problem 
    and calculate the quasiparticle energy once it is fed with 
    resigma = \omega - \epsilon_H - \Re\Sigma. 
    It expects an array of increasing values on the x axis 
    and it will return 
    the x value of the last resigma=0 detected. 
    It should return the value of eqp and the number of zeros
    found (useful in case there are plasmarons or for debugging). 
    If no zeros are found, it will fit resigma with a line and 
    extrapolate a value.
    """
    nzeros = 0
    zeros = []
    tmpeqp = en[0]
    tol_fermi = 1e-3
    for i in xrange(1,np.size(resigma)):
        #print(resigma[i]*resigma[i-1] # DEBUG)
        if  resigma[i] == 0: # Yes, it can happen
            tmpeqp = en[i] 
            zeros.append(en[i])
            nzeros+=1
        elif (resigma[i]*resigma[i-1] < 0):
            tmpeqp = en[i-1] - resigma[i-1]*(en[i] - en[i-1])/(resigma[i] - resigma[i-1]) # High school formula
            zeros.append(tmpeqp)
            nzeros+=1
    if tmpeqp - efermi > tol_fermi: 
        tmpeqp=zeros[0]
    if nzeros==0 : 
        print()
        print (" WARNING: No eqp found! ")
        def fit_func(x, a, b): 
            return a*x + b
        from scipy.optimize import curve_fit
        params = curve_fit(fit_func, en, resigma)
        [a, b] = params[0]
        if -b/a < en[-1]:
            print("WTF!!! BYE!")
            sys.exit()
        tmpeqp = -b/a
        zeros.append(tmpeqp)
   # elif nzeros>1 : 
   #     print(" WARNING: Plasmarons")
    return tmpeqp, nzeros

def calc_eqp_imeqp(bdrange, kptrange, en,enmin, enmax, res, ims, hartree, efermi, nkpt, nband, scgw, Elda):
    """
    This function calculates qp energies and corresponding
    values of the imaginary part of sigma for a set of
    k points and bands. 
    The function find_eqp_resigma() is used here.
    eqp and imeqp are returned. 
    """
    from scipy import interp
    eqp = np.zeros((nkpt,nband))
    imeqp = np.zeros((nkpt,nband))
    hartree = np.array(hartree)
    outname = "eqp.dat"
    outfile2 = open(outname,'w')
    outname = "imeqp.dat"
    outfile3 = open(outname,'w')
    newdx = 0.005
    newen = np.arange(en[0], en[-1], newdx)
    #for ik in kptrange:
    #    for ib in bdrange:
    for ik in xrange(nkpt):
        for ib in xrange(nband):
            interpres = interp1d(en, res[ik,ib], kind = 'linear', axis = -1)
            #temparray = np.array(en - hartree[ik,ib] - res[ik,ib])
            tmpres = interpres(newen)
            temparray = np.array(newen - hartree[ik,ib] - tmpres)
            interpims = interp1d(en, ims[ik,ib], kind = 'linear', axis = -1)
            tempim = interpims(newen)
            # New method to overcome plasmaron problem
            eqp[ik,ib], nzeros = find_eqp_resigma(newen,temparray,efermi)
            if nzeros==0: 
                print()
                print(" WARNING: ik "+str(ik)+" ib "+str(ib)+". No eqp found!!!")
            if (eqp[ik,ib] > newen[0]) and (eqp[ik,ib] < newen[-1]): 
                #print(en[0], eqp[ik,ib], en[-1])
                if scgw == 1:
                    Elda_kb = eqp[ik,ib]
                else:
                    Elda_kb = Elda[ik,ib]
                imeqp[ik,ib] = interpims(Elda_kb)
          #  else:
          #      imeqp[ik,ib] = interp(eqp[ik,ib], en, ims[ik,ib])
          #  ## Warning if imaginary part of sigma < 0 (Convergence problems?)
            #if imeqp[ik,ib] <= 0 : # SKYDEBUG do we really need to worry about this?? 
            #    print()
            #    print(""" WARNING: im(Sigma(e_k)) <= 0 !!! ik ib e_k
            #          im(Sigma(e_k)) = """, ik+1, ib+1, eqp[ik,ib], imeqp[ik,ib])
            outfile2.write("%14.5f" % (eqp[ik,ib]))
            outfile3.write("%14.5f" % (imeqp[ik,ib]))

        outfile2.write("\n")
        outfile3.write("\n")
    outfile2.close()
    outfile3.close()
    return eqp, imeqp
def A_model_crc(x,eqpkb,beta1, beta2,wp, eta_crc):
    import math
    G=0
    m=0
    while m<20:
        G += np.exp(-beta1-beta2)*(math.pow(beta1+beta2,
                                           m)-math.pow(beta1,m))/math.factorial(m)*(1./(x-eqpkb+m*(abs(wp)-1j*eta_crc) -1j*eta_crc))
        m += 1
    return (1.0/(math.pi))*abs(G.imag)

def calc_crc (bdrange, bdgw_min, kptrange, FFTtsize, en,enmin, enmax,
                    eqp,imeqp, Elda, scgw, Eplasmon, ims, invar_den,
                    invar_eta, wtk, metal_valence):
    import numpy as np
    import pyfftw
    from numpy.fft import fftshift,fftfreq
    from scipy.interpolate import interp1d
    import csv
    print("calc_crc : :")
    metal_valence = 1
    ddinter = 0.005
    newen_toc = np.arange(enmin, enmax, ddinter)
    toc96_tot = np.zeros((np.size(newen_toc)))
    crc_tot = np.zeros((np.size(newen_toc)))
    tol_fermi = 1e-3
    #pdos = np.array(pdos)
    fftsize = FFTtsize
    outname = "Norm_check_crc.dat"
    outfile = open(outname,'w')
    for ik in kptrange:
        ikeff = ik + 1
        for ib in bdrange:
            ibeff = ib + bdgw_min
            print(" ik, ib:",ikeff, ibeff)
            eqp_kb = eqp[ik, ib]
            imeqp_kb = imeqp[ik, ib]
            if scgw == 1:
                Elda_kb = eqp[ik, ib]
            else:
                Elda_kb = Elda[ik, ib]
            print("eqp:", eqp_kb)
            print("Elda:", Elda_kb)
            if eqp_kb <= tol_fermi:
                Done = False
                Es2 = 0
                while not Done:
                    if -2*Eplasmon <= en[-1]:
                        NewEn_min = int(-2*Eplasmon + Es2)
                    else:
                        NewEn_min = int(-2*Eplasmon - Es2)
                    Es2 += 1
                    if NewEn_min > en[0] and NewEn_min + Elda_kb > en[0]:
                        Done = True
                Done_max = False
                Es = 0
                while not Done_max:
                    NewEn_max = -Elda_kb - Es
                    Es += 1
                    if NewEn_max < en[-1] and NewEn_max+Elda_kb < en[-1]:
                        Done_max = True

                Done_max_crc = False
                Es_crc = 0
                while not Done_max_crc:
                    NewEn_max_crc = en[-1] - Es
                    Es_crc += 1
                    if NewEn_max_crc < en[-1] and NewEn_max_crc+Elda_kb < en[-1]:
                        Done_max_crc = True
                if metal_valence == 1:
                    NewEn_max = -Elda_kb #-0.005
                tfft_min = -2*np.pi/invar_den
                tfft_max = 0
                trange = np.linspace(tfft_min, tfft_max, fftsize)
                dtfft = abs(trange[-1]-trange[0])/fftsize
                print ("the time step is", dtfft)
                print("the size of fft is", fftsize)
                interpims = interp1d(en, ims[ik,ib], kind = 'linear', axis
                                         = -1)
                gt_list = []
                newdx = invar_den  # must be chosen carefully so that 0 is
                # included in NewEn. invar_den can be 0.1*0.5^n, or 0.2. 
                NewEn_0 = np.arange(NewEn_min, NewEn_max, newdx)
                NewEn = [x for x in NewEn_0 if abs(x) > 1e-6]
                NewEn = np.asarray(NewEn)
                NewEn_greater = np.arange(NewEn_max+1, NewEn_max_crc, newdx)
                NewEn_crc =  np.arange(NewEn_min, NewEn_max_crc, newdx)
                print("SKYDEBUG NewEn_crc", NewEn_crc[0], NewEn_crc[-1])
                NewEn_size = len(NewEn)
                if NewEn[-1]>=0 and NewEn_size == len(NewEn_0):
                    print("""Zero is not in the intergration of ImSigma(w),
                          please check invar_den""")

                    sys.exit(0)
                ShiftEn = NewEn + Elda_kb #np.arange(NewEn_min + Elda_kb, NewEn_max
                ShiftIms = interpims(ShiftEn)
                ShiftIms_0 = interpims(NewEn_0+Elda_kb)
                ShiftIms_crc = interpims(NewEn_greater + Elda_kb )/np.pi
                #bcrc = 0
                #for i in xrange(len(NewEn_greater)):
                #    bcrc += abs(ShiftIms_crc[i])/((NewEn_greater[i])**2)
                #    
                #B_crc_new = bcrc
                #print("SKYDEBUG Bcrc",  B_crc_new)
                im_greater = abs(interpims(NewEn_greater))/np.pi
                en_greater = NewEn_greater - Elda_kb
                omega_greater, lambda_greater, delta_greater = fit_multipole_const(en_greater,im_greater,1)
                beta_greater = map(abs,lambda_greater)/(omega_greater)**2
                im_lesser =  abs(interpims(NewEn))/np.pi 
                en_lesser = NewEn - Elda_kb
                omega_lesser, lambda_lesser, delta_lesser = fit_multipole_const(en_lesser,im_lesser,1)
                beta_lesser = map(abs,lambda_lesser)/(omega_lesser)**2
                #print("SKYDEBUG beta_greater", beta_greater,np.exp(-beta_greater))

                #print("SKYDEBUG beta_lesser", beta_lesser, np.exp(-beta_lesser))
                #with open("ShiftIms_toc-k"+str("%02d"%(ikeff))+"-b"+str("%02d"%(ibeff))+".dat", 'w') as f:
                #    writer = csv.writer(f, delimiter = '\t')
                #    writer.writerows(zip (NewEn_0, ShiftIms_0))
                for t in trange:
                    tImag = t*1.j 
                    area_tmp1 = 1.0/np.pi*abs(ShiftIms)*(np.exp(-(NewEn)*tImag)-1.0)*(1.0/((NewEn)**2))
                    ct_tmp1 = np.trapz(area_tmp1, NewEn)

                    ct_tot = ct_tmp1 
                    gt_tmp = np.exp(ct_tot)
                    gt_list.append(gt_tmp)

                denfft = 2*np.pi/abs(trange[-1]-trange[0])
                print("the energy resolution after FFT is",denfft)
                fften_min = -2*np.pi/dtfft
                fften_max = 0
                enrange = np.arange(fften_min,NewEn[-1],denfft)
                print("IFFT of ")
                print("kpoint = %02d" % (ikeff))
                print("band=%02d" % (ibeff))

                fft_in = pyfftw.empty_aligned(fftsize, dtype='complex128')
                fft_out = pyfftw.empty_aligned(fftsize, dtype='complex128')
                ifft_object = pyfftw.FFTW(fft_in, fft_out,
                                  direction='FFTW_BACKWARD',threads
                                          = 1)
                cw=ifft_object(gt_list)*(fftsize*dtfft)

                freq = fftfreq(fftsize,dtfft)*2*np.pi
                s_freq = fftshift(freq)  
                s_go = fftshift(cw)
                eta = 1.j*invar_eta
                w_list = np.arange(enmin,newen_toc[-1]+denfft,denfft)
                gw_list = []
                for w in w_list:
                    Area2 = s_go/(w-eqp_kb-s_freq-eta) 
                    c = np.trapz(Area2, dx = denfft)
                    cwIm = 1./np.pi*c.imag
                    gw_list.append(0.5*wtk[ik]*np.exp(-beta_greater[0])/np.pi*cwIm)

                print("IFFT done .....")
                interp_toc = interp1d(w_list, gw_list, kind='linear', axis=-1)
                interp_en = newen_toc

                spfkb = interp_toc(interp_en)
                toc96_tot += spfkb
                with open("TOC96-k"+str("%02d"%(ikeff))+"-b"+str("%02d"%(ibeff))+".dat", 'w') as f:
                    writer = csv.writer(f, delimiter = '\t')
                    writer.writerows(zip (interp_en, spfkb))
                #outnamekb = "TOC11-k"+str("%02d"%(ikeff))+"-b"+str("%02d"%(ibeff))+".dat"
                #outfilekb = open(outnamekb,'w')
                #en_toc11 = []
                #for i in xrange(len(interp_en)):
                #    en_toc11.append(interp_en[i])
                #    outfilekb.write("%8.4f %12.8e \n" % (interp_en[i],spfkb[i])) 
                #outfilekb.close()
                Gw_unocc = wtk[ik]* A_model_crc(interp_en, eqp_kb ,beta_lesser[0],
                                       beta_greater[0],omega_lesser,
                                       imeqp_kb+eta) 
                crc_tot += spfkb+Gw_unocc
                with open("CRC_unocc"+str("%02d"%(ikeff))+"-b"+str("%02d"%(ibeff))+".dat", 'w') as f:
                    writer = csv.writer(f, delimiter = '\t')
                    writer.writerows(zip (interp_en, Gw_unocc))
                
                print("calculate occupation from TOC96 : :")
                norm = np.trapz(spfkb,interp_en)/(wtk[ik])
                print("The occupation for ik, ib, is", ikeff, ibeff, norm)
    
                outfile.write("%8.4f %12.8e \n" % (newdx, norm))
    outfile.close()
    return interp_en, toc96_tot, crc_tot

def calc_toc11_new (bdrange, bdgw_min, kptrange, FFTtsize, en,enmin, enmax,
                    eqp, Elda, scgw, Eplasmon, ims, invar_den,
                    invar_eta, wtk, metal_valence):
    import numpy as np
    import pyfftw
    from numpy.fft import fftshift,fftfreq
    from scipy.interpolate import interp1d
    import csv
    print("calc_toc11 : :")
    if metal_valence ==1:
        print("""
              WARNING: You are using TOC to calculate valence
              band of metal !! Please be sure that in SIG file,
              the maximum energy covers all -eqp_kb, otherwise, 
              the code might not run !!!
              """)
    ddinter = 0.005 
    newen_toc = np.arange(enmin, enmax, ddinter)
    toc_tot =  np.zeros((np.size(newen_toc))) 
    #pdos = np.array(pdos)
    tol_fermi = 1e-3
    fftsize = FFTtsize
    outname = "Norm_check_toc11.dat"
    outfile = open(outname,'w')
    for ik in kptrange:
        ikeff = ik + 1
        for ib in bdrange:
            ibeff = ib + bdgw_min
            print(" ik, ib:",ikeff, ibeff)
            eqp_kb = eqp[ik, ib]
            if scgw == 1:
                Elda_kb = eqp[ik, ib]
            else:
                Elda_kb = Elda[ik, ib]
            print("eqp:", eqp_kb)
            print("Elda:", Elda_kb)
            if eqp_kb <= tol_fermi:
                Done = False
                Es2 = 0
                while not Done:
                    if -2*Eplasmon <= en[-1]:
                        NewEn_min = int(-2*Eplasmon + Es2)
                    else:
                        NewEn_min = int(-2*Eplasmon - Es2)
                    Es2 += 1
                    if NewEn_min > en[0] and NewEn_min + Elda_kb > en[0]:
                        Done = True
                Done_max = False
                Es = 0
                while not Done_max:
                    NewEn_max = -Elda_kb - Es
                    Es += 1
                    if NewEn_max < en[-1] and NewEn_max+Elda_kb < en[-1]:
                        Done_max = True
                if metal_valence == 1:
                    NewEn_max = -Elda_kb #-0.005
                tfft_min = -2*np.pi/invar_den
                tfft_max = 0
                trange = np.linspace(tfft_min, tfft_max, fftsize)
                dtfft = abs(trange[-1]-trange[0])/fftsize
                print ("the time step is", dtfft)
                print("the size of fft is", fftsize)
                interpims = interp1d(en, ims[ik,ib], kind = 'linear', axis
                                         = -1)
                imeqp_kb = interpims(eqp_kb)
                print("ImSigma(eqp)", imeqp_kb)
                gt_list = []
                newdx = invar_den  # must be chosen carefully so that 0 is
                # included in NewEn. invar_den can be 0.1*0.5^n, or 0.2. 
                NewEn_0 = np.arange(NewEn_min, NewEn_max, newdx)
                NewEn = [x for x in NewEn_0 if abs(x) > 1e-6]
                NewEn = np.asarray(NewEn)
                NewEn_size = len(NewEn)
                if NewEn[-1]>=0 and NewEn_size == len(NewEn_0):
                    print("""Zero is not in the intergration of ImSigma(w),
                          please check invar_den""")

                    sys.exit(0)
                ShiftEn = NewEn + Elda_kb #np.arange(NewEn_min + Elda_kb, NewEn_max
                ShiftIms = interpims(ShiftEn)
                ShiftIms_0 = interpims(NewEn_0+Elda_kb)
                #with open ('Encut.dat', 'w') as f:
                #    writer = csv.writer(f, delimiter = '\t')
                #    writer.writerows(zip (NewEn, ShiftIms))
                with open("ShiftIms_toc-k"+str("%02d"%(ikeff))+"-b"+str("%02d"%(ibeff))+".dat", 'w') as f:
                    writer = csv.writer(f, delimiter = '\t')
                    writer.writerows(zip (NewEn_0, ShiftIms_0))
                for t in trange:
                    tImag = t*1.j 
                    area_tmp1 = 1.0/np.pi*abs(ShiftIms)*(np.exp(-(NewEn)*tImag)-1.0)*(1.0/((NewEn)**2))
                    ct_tmp1 = np.trapz(area_tmp1, NewEn)

                    ct_tot = ct_tmp1 
                    gt_tmp = np.exp(ct_tot)
                    gt_list.append(gt_tmp)

                denfft = 2*np.pi/abs(trange[-1]-trange[0])
                print("the energy resolution after FFT is",denfft)
                fften_min = -2*np.pi/dtfft
                fften_max = 0
                enrange = np.arange(fften_min,NewEn[-1],denfft)
                print("IFFT of ")
                print("kpoint = %02d" % (ikeff))
                print("band=%02d" % (ibeff))

                fft_in = pyfftw.empty_aligned(fftsize, dtype='complex128')
                fft_out = pyfftw.empty_aligned(fftsize, dtype='complex128')
                ifft_object = pyfftw.FFTW(fft_in, fft_out,
                                  direction='FFTW_BACKWARD',threads
                                          = 1)
                cw=ifft_object(gt_list)*(fftsize*dtfft)

                freq = fftfreq(fftsize,dtfft)*2*np.pi
                s_freq = fftshift(freq)  
                s_go = fftshift(cw)
                eta = 1.j*invar_eta
                w_list = np.arange(enmin,newen_toc[-1]+denfft,denfft)
                gw_list = []
                for w in w_list:
                    Area2 = s_go/(w-eqp_kb-s_freq-eta) 
                    c = np.trapz(Area2, dx = denfft)
                    cwIm = 1./np.pi*c.imag
                    gw_list.append(0.5*wtk[ik]/np.pi*cwIm)

                print("IFFT done .....")
                interp_toc = interp1d(w_list, gw_list, kind='linear', axis=-1)
                interp_en = newen_toc

                spfkb = interp_toc(interp_en)
                toc_tot += spfkb
                with open("TOC11-k"+str("%02d"%(ikeff))+"-b"+str("%02d"%(ibeff))+".dat", 'w') as f:
                    writer = csv.writer(f, delimiter = '\t')
                    writer.writerows(zip (interp_en, spfkb))
                #outnamekb = "TOC11-k"+str("%02d"%(ikeff))+"-b"+str("%02d"%(ibeff))+".dat"
                #outfilekb = open(outnamekb,'w')
                #en_toc11 = []
                #for i in xrange(len(interp_en)):
                #    en_toc11.append(interp_en[i])
                #    outfilekb.write("%8.4f %12.8e \n" % (interp_en[i],spfkb[i])) 
                #outfilekb.close()
                norm = np.trapz(spfkb,interp_en)/(wtk[ik])
                print("check the renormalization : :")
                print()
                print("the normalization of the spectral function is",norm)
                if abs(1-norm)>0.01:
                    print("WARNING: the renormalization is too bad!\n"+\
                          "Increase the time size to converge better.", ikeff,ibeff)
    
                outfile.write("%8.4f %12.8e \n" % (newdx, norm))
    outfile.close()
    return interp_en, toc_tot

def calc_rc (bdrange, bdgw_min, kptrange, FFTtsize, en,enmin, enmax,
                    eqp, Elda, scgw, encut, ims, invar_den, invar_eta, wtk):
    import numpy as np
    import pyfftw
    import csv
    from numpy.fft import fftshift,fftfreq
    from scipy.interpolate import interp1d
    print("calc_rc : :")

    ddinter = 0.005 
    newen_rc = np.arange(enmin, enmax, ddinter)
    rc_tot =  np.zeros((np.size(newen_rc))) 
    #pdos = np.array(pdos)
    fftsize = FFTtsize
    outname = "Norm_check_rc.dat"
    outfile = open(outname,'w')

    for ik in kptrange:
        ikeff = ik + 1
        for ib in bdrange:
            ibeff = ib + bdgw_min
            print(" ik, ib:",ikeff, ibeff)
            eqp_kb = eqp[ik, ib]
            if scgw == 1:
                Elda_kb = eqp[ik, ib]
            else:
                Elda_kb = Elda[ik, ib]
            print("eqp:", eqp_kb)
            print("Elda:", Elda_kb)
            Done = False
            Es2 = 0
            while not Done:
                NewEn_min = int(en[0] + Es2)
                Es2 += 1
                if NewEn_min > en[0] and NewEn_min + Elda_kb > en[0]:
                    Done = True
            Done_max = False
            Es = 0
            while not Done_max:
                NewEn_max = en[-1] - Es
                Es += 1
                if NewEn_max < en[-1] and NewEn_max+Elda_kb < en[-1]:
                    Done_max = True
            tfft_min = -2*np.pi/invar_den
            tfft_max = 0
            trange = np.linspace(tfft_min, tfft_max,fftsize)
            dtfft = abs(trange[-1]-trange[0])/fftsize
            print ("the time step is", dtfft)
            print("the size of fft is", fftsize)
            interpims = interp1d(en, ims[ik,ib], kind = 'linear', axis=-1)
            newdx = invar_den  # must be chosen carefully so that 0 is
            # included in NewEn. invar_den can be 0.1*0.5^n, or 0.2. 
            NewEn_0 = np.arange(NewEn_min, NewEn_max, newdx)
            
            NewEn = [x for x in NewEn_0 if abs(x) > 1e-6]
            NewEn = np.asarray(NewEn)
            NewEn_size = len(NewEn)
            if NewEn_size == len(NewEn_0):
                print("""invar_den should  be 0.1*0.5*n where n is
                      integer number!!!""")

                sys.exit(0)
            ShiftEn = NewEn + Elda_kb #np.arange(NewEn_min + Elda_kb, NewEn_max
            ShiftIms = interpims(ShiftEn)
            ShiftIms_0 = interpims(NewEn_0+Elda_kb)
            gt_list = []
            for t in trange:
                tImag = t*1.j 
                area_tmp = 1.0/np.pi*abs(ShiftIms)*(np.exp(-(NewEn)*tImag)-1.0)*(1.0/((NewEn)**2))
                ct_tmp = np.trapz(area_tmp, NewEn)
                gt_tmp = np.exp(ct_tmp)
                gt_list.append(gt_tmp)
            with open("ShiftIms_rc-k"+str("%02d"%(ikeff))+"-b"+str("%02d"%(ibeff))+".dat",
                                  'w') as f:
                writer = csv.writer(f, delimiter = '\t')
                writer.writerows(zip (NewEn, ShiftIms))

            denfft = 2*np.pi/abs(trange[-1]-trange[0])
            print("the energy resolution after FFT is",denfft)
            fften_min = -2*np.pi/dtfft
            fften_max = 0
            enrange = np.arange(fften_min,NewEn[-1],denfft)
            print("IFFT of ")
            print("kpoint = %02d" % (ikeff))
            print("band=%02d" % (ibeff))

            fft_in = pyfftw.empty_aligned(fftsize, dtype='complex128')
            fft_out = pyfftw.empty_aligned(fftsize, dtype='complex128')
            ifft_object = pyfftw.FFTW(fft_in, fft_out,
                              direction='FFTW_BACKWARD',threads
                                      = 1)
            cw=ifft_object(gt_list)*(fftsize*dtfft)

            freq = fftfreq(fftsize,dtfft)*2*np.pi
            s_freq = fftshift(freq)  
            s_go = fftshift(cw)

            eta = 1.j*invar_eta #the eta in the theta function 
            gw_list = []
            w_list = np.arange(enmin,newen_rc[-1]+denfft,denfft)
            for w in w_list:
                Area2 = s_go/(w-eqp_kb-s_freq-eta) 
                c = np.trapz(Area2, dx = denfft)
                #c = 0
                #for i in xrange(fftsize-1):
                #    Area2 = 0.5*denfft*(s_go[i]/(w-eqp_kb-s_freq[i]-eta)
                #                + s_go[i+1]/(w-eqp_kb-s_freq[i+1]-eta))
                #    c += Area2
                cwIm = 1./np.pi*c.imag
                gw_list.append(0.5*wtk[ik]/np.pi*cwIm)

            print("IFFT done .....")
            interp_toc = interp1d(w_list, gw_list, kind='linear', axis=-1)
            interp_en = newen_rc
            #print("""the new energy range is (must be inside of above
             #     range)""",interp_en[0], interp_en[-1])
            spfkb = interp_toc(interp_en)
            rc_tot += spfkb
            with open ("spf_rc-k"+str("%02d"%(ikeff))+"-b"+str("%02d"%(ibeff))+".dat",'w') as f:
                writer = csv.writer(f, delimiter = '\t')
                writer.writerows(zip(interp_en, spfkb))
            #spfkb = gw_list
            #toc_tot = [sum(i) for i in zip(toc_tot,gw_list)]
            #outnamekb = "spf_rc-k"+str("%02d"%(ikeff))+"-b"+str("%02d"%(ibeff))+".dat"
            #outfilekb = open(outnamekb,'w')
            #en_toc11 = []
            #for i in xrange(len(interp_en)):
            #    en_toc11.append(interp_en[i])
            #    outfilekb.write("%8.4f %12.8e \n" % (interp_en[i],spfkb[i])) 
            #outfilekb.close()
            norm = np.trapz(spfkb,interp_en)/(wtk[ik])
            print("check the renormalization : :")
            print()
            print("the normalization of the spectral function is",norm)
            if abs(1-norm)>0.01:
                print("WARNING: the renormalization is too bad!\n"+\
                      "Increase the time size to converge better.", ikeff,ibeff)
    
            outfile.write("%8.4f %12.8e \n" % (newdx, norm))
    outfile.close()
    return interp_en, rc_tot