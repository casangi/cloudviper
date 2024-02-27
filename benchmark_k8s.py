#pip install cngi_prototype==0.0.51
#pip install ngcasa==0.0.7
#numba might not be installed correctly

#export OMP_NUM_THREADS=1
#export MKL_NUM_THREADS=1
#export OPENBLAS_NUM_THREADS=1

if __name__ == '__main__':
    import os, time
    import xarray as xr
    from dask.distributed import Client
    import dask.array as da
    from ngcasa.synthesis.imaging import make_dirty_image
    import zarr
    import s3fs
    
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    
    # Initialize the S3 "file system"
    s3 = s3fs.S3FileSystem(anon=True, requester_pays=False)

    # Specify AWS S3 paths
    bucket = "cngi-prototype-test-data/"
    s3_path = bucket
    #s3_path = bucket+"test_data/"

    if s3.isdir(s3_path): # it's working
        print("Files available for access:")
        print(s3.listdir(s3_path))

    ddi = "0"
    s3_vis = s3_path+"combined_spw_uid___A002_Xcb8a93_Xc096.vis.zarr/"+ddi
    s3_metadata = s3_path+"combined_spw_uid___A002_Xcb8a93_Xc096.vis.zarr/global"

    # Convert object stores to our desired MutableMapping interface
    store_vis = s3fs.S3Map(root=s3_vis, s3=s3, check=False)
    #store_global = s3fs.S3Map(root=s3_metadata, s3=s3, check=False)
    
    vis_dataset = xr.open_zarr(store=store_vis, chunks={'time':782,'chan':40}, consolidated=True)
    #global_dataset = xr.open_zarr(store=store_global, consolidated=True)
        
    grid_parms = {
        'chan_mode'           : 'cube', # or 'continuum'
        'imsize'              :  [428,428],
        'cell'                : [0.02, 0.02],
        'oversampling'        : 100, # 100
        'support'             : 7, #71
        'fft_padding'         : 1.2,
        'imaging_weight_name' : 'IMAGING_WEIGHT_CUBE_NOFLAG', #'IMAGING_WEIGHT_CONT_NOFLAG'
        'image_name'          : 'DIRTY_IMAGE_CUBE_NOFLAG', #'DIRTY_IMAGE_CONT_NOFLAG'
        }
    
    #Set storage parms
    storage_parms = {
        'to_disk': True,
        'append' : False,
        'outfile' : 'data/cube_image_A002_Xcb8a93_Xc096.img.zarr', # 'data/cont_image_A002_Xcb8a93_Xc096.img.zarr'
        #'compressor' : Blosc(cname='zstd', clevel=2, shuffle=0),
        }

    memory_limit = '200GB'
    max_threads = 96
    n_worker = 1
    
    for i in range(max_threads, 8-1, -4):
        bench_file = open('combined_spw_uid___A002_Xcb8a93_Xc096.txt','a')
        print(i)
        threads_per_worker = i
        
        client = Client(n_workers=n_worker, threads_per_worker=threads_per_worker, memory_limit=memory_limit)
        print(client.scheduler_info()['services'])
        start = time.time()
        img_dataset = make_dirty_image(vis_dataset,grid_parms,storage_parms)
        time_to_calc_and_store = time.time() - start
        client.close()
         
        bench_file.write(" %d %d %f \r\n" % (n_worker,threads_per_worker,time_to_calc_and_store))
        bench_file.close()
    











