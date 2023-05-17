'''
Marina Fresneda Manzano 
 T5 - Sonido estéreo y ficheros WAVE
'''

import struct as st


def estereo2mono(ficEste, ficMono, canal=2):
    """
    Convierte un archivo estéreo en un archivo monofónico
    """
    with open(ficEste, 'rb') as fpwave:
        cabecera1 = '<4sI4s'
        buffer1 = fpwave.read(st.calcsize(cabecera1))

        cabecera2 ='<4sI2H2I2H'
        buffer2 = fpwave.read(st.calcsize(cabecera2))
        (ChunkID2, ChunkSize2, format2, numchannels, samplerate, byterate, blockalign, bitspersample)   = st.unpack(cabecera2,buffer2)

        cabecera3 = '<4sI'
        buffer3 = fpwave.read(st.calcsize(cabecera3))
        ChunkID3, ChunkSize3 = st.unpack(cabecera3,buffer3)
        nummuestras = ChunkSize3 // blockalign
       
        formato = f'<{nummuestras*2}h'
        size = st.calcsize(formato)
        buffer4 = fpwave.read(size)
        datos = st.unpack(formato,buffer4)

    with open(ficMono,'wb') as fout:
        cabecera_fmt = '<4sI4s4sIHHIIHH4sI'
        cabecera = (b'RIFF', 36 + nummuestras * blockalign, b'WAVE', b'fmt ', 16, 1, 1, samplerate, byterate // numchannels , blockalign // numchannels, bitspersample, b'data', nummuestras * 2)
        pack1 = st.pack(cabecera_fmt, *cabecera)
        fout.write(pack1)

        if bitspersample == 16:
            formato = 'h'
        else:
            formato = 'b'
        if canal in [0, 1]:
            for iter in range(nummuestras):
                muestra = datos[iter * 2 + canal]
                fout.write(st.pack(formato, muestra))
        else:
            if canal == 2:
                for iter in range(nummuestras):
                    muestra = (datos[2 * iter] + datos[iter * 2 + 1]) // 2
                    fout.write(st.pack(formato, muestra))
            else:
                for iter in range(nummuestras):
                    muestra = (datos[2 * iter] - datos[iter * 2 + 1]) // 2
                    fout.write(st.pack(formato, muestra))


def mono2stereo(ficIzq, ficDer, ficEste):
    """
    Convierte un archivo monofónico en un archivo estéreo
    """
    with open(ficIzq, 'rb') as fin:
        cabecera1 = '<4sI4s'
        buffer1 = fin.read(st.calcsize(cabecera1))

        cabecera2 = '<4sI2H2I2H'
        buffer2 = fin.read(st.calcsize(cabecera2))
        ChunkID2, ChunkSize2, format2, numchannels, samplerate, byterate, blockalign, bitspersample = st.unpack(cabecera2, buffer2)

        cabecera3 = '<4sI'
        buffer3 = fin.read(st.calcsize(cabecera3))
        ChunkID3, ChunkSize3 = st.unpack(cabecera3, buffer3)
        nummuestras = ChunkSize3 // blockalign

        with open(ficDer, 'rb') as fin_der:
            with open(ficEste, 'wb') as fout:
                cabecera_fmt = '<4sI4s4sIHHIIHH4sI'
                cabecera = (b'RIFF', 36 + nummuestras * blockalign * 2, b'WAVE', b'fmt ', 16, 1, 2, samplerate, byterate // numchannels, blockalign // numchannels, bitspersample, b'data', nummuestras * 2 * 2)
                pack1 = st.pack(cabecera_fmt, *cabecera)
                fout.write(pack1)

                if bitspersample == 16:
                    formato = 'h'
                else:
                    formato = 'b'

                for iter in range(nummuestras):
                    muestra_izq = st.unpack(formato, fin.read(st.calcsize(formato)))[0]
                    muestra_der = st.unpack(formato, fin_der.read(st.calcsize(formato)))[0]

                    fout.write(st.pack(formato, muestra_izq))
                    fout.write(st.pack(formato, muestra_der))


def codEstereo(ficEste, ficCod):
    """
    Construye una señal codificada con 32 bits que permita su reproducción tanto por sistemas monofónicos como por sistemas estéreo
    
    """
    with open(ficEste, 'rb') as fpwave:
        cabecera1 = '<4sI4s'
        ChunkID, ChunkSize, format = st.unpack(cabecera1, fpwave.read(st.calcsize(cabecera1)))
        if ChunkID != b'RIFF' or format != b'WAVE':
            raise Exception('Fichero no es wave') from None

        cabecera2 = '<4sI2H2I2H'
        (ChunkID2, ChunkSize2, format2, numchannels, samplerate, byterate, blockalign, bitspersample) = st.unpack(
            cabecera2, fpwave.read(st.calcsize(cabecera2)))
        if numchannels != 2:
            raise Exception('Fichero no estereo') from None

        cabecera3 = '<4sI'
        (ChunkID3, ChunkSize3) = st.unpack(cabecera3, fpwave.read(st.calcsize(cabecera3)))
        nummuestras = ChunkSize3 // blockalign

        formato = f'<{nummuestras * 2}h'
        size = st.calcsize(formato)
        datos = st.unpack(formato, fpwave.read(size))

    datosL = []
    datosR = []

    for iter in range(nummuestras):
        datosL.append(datos[2 * iter])
        datosR.append(datos[iter * 2 + 1])

    datos_cod = bytearray()
    for muestraL, muestraR in zip(datosL, datosR):
        semisuma = (muestraL + muestraR) // 2
        semidif = (muestraL - muestraR) // 2
        muestracod = (semisuma << 16) | (semidif >> 16)
        datos_cod.extend(st.pack('<i', muestracod))

    with open(ficCod, 'wb') as fout:
        cabecera_fmt = '<4sI4s4sIHHIIHH4sI'
        cabecera = (b'RIFF', 36 + nummuestras * 4, b'WAVE', b'fmt ', 16, 1, 2, 16000, 64000, 4, 16, b'data', nummuestras * 4)
        fout.write(st.pack(cabecera_fmt, *cabecera))
        fout.write(datos_cod)


def decEstereo(ficCod, ficEste):
    """
    Lee un fichero de señal codificada en 32 bits y escribe los canales de una señal estéreo 
    """
    with open(ficCod, 'rb') as fpwave:
        cabecera1 = '<4sI4s'
        ChunkID, ChunkSize, format = st.unpack(cabecera1, fpwave.read(st.calcsize(cabecera1)))
        if ChunkID != b'RIFF' or format != b'WAVE':
            raise Exception('Fichero no es wave') from None

        cabecera2 = '<4sI2H2I2H'
        (ChunkID2, ChunkSize2, format2, numchannels, samplerate, byterate, blockalign, bitspersample) = st.unpack(
            cabecera2, fpwave.read(st.calcsize(cabecera2)))
        if numchannels != 2:
            raise Exception('Fichero no estereo') from None

        cabecera3 = '<4sI'
        (ChunkID3, ChunkSize3) = st.unpack(cabecera3, fpwave.read(st.calcsize(cabecera3)))
        nummuestras = ChunkSize3 // blockalign

        formato = f'<{nummuestras}i'
        size = st.calcsize(formato)
        datoscod = st.unpack(formato, fpwave.read(size))

        datosL = []
        datosR = []

        for i in range(nummuestras):
            semisuma = (datoscod[i] >> 16)
            semidif = datoscod[i] & 0x0000ffff
            muestraR = (semisuma - semidif)
            muestraL = (semidif + semisuma)
            datosL.append(muestraL)
            datosR.append(muestraR)

    with open(ficEste, 'wb') as fout:
        cabecera_fmt = '<4sI4s4sIHHIIHH4sI'
        cabecera = (b'RIFF', 36 + nummuestras * 4, b'WAVE', b'fmt ', 16, 1, 2, 16000, 64000, 4, 16, b'data', nummuestras * 4)
        fout.write(st.pack(cabecera_fmt, *cabecera))

        for muestra_L, muestra_R in zip(datosL, datosR):
            muestracod = muestra_L << 16 | muestra_R
            fout.write(st.pack('<i', muestracod))



estereo2mono('wav\komm.wav','wav\kommMono1.wav',canal=1)
estereo2mono('wav\komm.wav','wav\kommMono0.wav',canal=0)
estereo2mono('wav\komm.wav','wav\kommMono2.wav',canal=2)

mono2stereo("wav\kommMono0.wav","wav\kommMono1.wav","wav\kommStOut.wav")


codEstereo('wav\komm.wav','wav\kommCodec.wav')
decEstereo('wav\kommCodec.wav','wav\kommDeCodec.wav')