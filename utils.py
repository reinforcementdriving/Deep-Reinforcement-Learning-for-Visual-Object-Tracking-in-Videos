# -*- coding: utf-8 -*-


from common import *

#%% Recalculate x,y,w,h to the four corner coordinates
    
def calc_coords(gt_wh):
    gt_new = np.zeros((gt_wh.shape[0],8))
    print(gt_new.shape)
    print(gt_wh.shape)
    print(gt_wh[:,0])
    gt_new[:,0] = gt_wh[:,0]                # x1
    gt_new[:,1] = gt_wh[:,1]                # y1
    gt_new[:,2] = gt_wh[:,0] + gt_wh[:,2]   # x2
    gt_new[:,3] = gt_wh[:,1]                # y2
    gt_new[:,4] = gt_wh[:,0] + gt_wh[:,2]   # x3
    gt_new[:,5] = gt_wh[:,1] + gt_wh[:,3]   # y3  
    gt_new[:,6] = gt_wh[:,0]                # x4
    gt_new[:,7] = gt_wh[:,1] + gt_wh[:,3]   # y4
    
    return gt_new
#%% Dataset class
    
'''Output is the imagesequence in an np.array format and the gt aswell.'''

class VOT2017_dataset(Dataset):
    """This is the VOT2017 dataset"""
    def __init__(self, csv_file, root_dir, transform = None):
        """ Arguments:
            csv_file(string): Path to list file, where all videos are listed
            root_dir(string): Directory with all the videos
            transform(callable, optional): Will transform on a sample(for pytorch I guess)
        """
        self.vot_list = pd.read_csv(csv_file, header = None)
        self.root_dir = root_dir
        self.transform = transform
    
    # Returns the nr of videos available
    def __len__(self):
        return len(self.vot_list)
    
    # Return the complete video sequence
    def __getitem__(self, vid_idx):
        """ Arguments:
            vid_idx(int): Video Index to be fetched form the video list
        """
        vid_name_path = os.path.join(self.root_dir, 
                                     self.vot_list.iloc[vid_idx,0],
                                     '*.jpg')
        
        gt = pd.read_csv(os.path.join(self.root_dir, 
                                      self.vot_list.iloc[vid_idx,0],
                                      'groundtruth.txt'), header = None)
        
        im_seq = imread_collection(vid_name_path)
        
        # Image collection to np.array
        images = concatenate_images(im_seq) # Shape(Nr. of images, h, w, RGB)
        
        # Also convert the gt to np.array
        gt = gt.values
        
        if gt.shape[1] == 4:
            gt = calc_coords(gt)
            
        
        sample = {'Video': images, 'gt': gt}
        
        # Cant tell yet what this is for
        if self.transform:
            sample = self.transform(sample)    
        return sample


#%%
        
# Draws a rectangle given the coordinates of all four corners in one array
# Where the order is upper-left, upper-right, lower-rigth, lower-left
def draw_gt(im, coords):
    """ Arguments:
            im = image
            coords = coords of all corners as in ground truth files(u.l,u.r,l.r,l.l)(u=upper,l = lower)
        """
    plt.imshow(im)
    Xs = coords[::2] # Save Xcoords
    Ys = coords[1::2] # Save Ycoords
    for i in range(4):
        if i < 3:
            plt.plot([Xs[i],Xs[i+1]],[Ys[i],Ys[i+1]],'k-', color = 'r',lw=1)
        elif i == 3:
            plt.plot([Xs[i],Xs[0]],[Ys[i],Ys[0]],'k-', color ='r', lw=1)
    plt.show()
    

#%% Transforms - Rescale/Resize
    
# Rescaling of an image so that we can feed it with the same size into a network
# Also the groundtruth boxes have to be rescaled accordingly!
# Problem atm rescale the whole Video!! - so far only with for loop

class Rescale(object):
    '''
    Rescale the image in a sample to a given size
    
    Arguments: output_size(tuple): Desired output size
               idx(int) : For now idx of the image to be resized
    '''
    
    # Check if output_size is a tuple,
    # maybe also assert if it isnt bigger than the smallest image?
    def __init__(self, output_size):
        assert isinstance(output_size,(tuple))
        self.output_size = output_size
        
    def __call__(self, sample):
        # Split the sample in video and gt
        images, gt = sample['Video'], sample['gt']
        nr = len(images) # Save the amount of images to iterate over
        print(nr)
        # Save heigth and widthim of video
        h, w = images.shape[1:3] # heigth and width are the 2nd and 3rd entry
        
        new_h, new_w = self.output_size
        
        
        # I dont like this part due to the for loop.! 
        # Initialize the resized image sequence array
        img = np.zeros((nr,new_h,new_w, images.shape[3]))
        # Iterate over all images and resize them to the given scale.
        for i in range(nr):
            img[i,:,:,:] = transform.resize(images[i,:,:,:], (new_h, new_w))
        
    
        # Here the groundtruth boxes are rescaled aswell
        gt_new = gt*np.array((new_w/w, new_h/h, new_w/w,new_h/h, new_w/w,new_h/h, new_w/w, new_h/h))
        
        return {'Video': img, 'gt': gt_new}

#%% Transforms - ToTensor

# Transform the loaded image collection to Tensors

class ToTensor(object):
    '''Convert sample to tensor'''
    def __call__(self, sample):
        # Load the sample and split it
        images, gt = sample['Video'], sample['gt']
        
        # swap color axis because
        # numpy image: H x W x C
        # torch image: C X H X W
        # How does this relate to videos/imagesequences?
        images = images.transpose((0,3,1,2))
        
        return {'Video': torch.from_numpy(images),
                'gt': torch.from_numpy(gt)}
    
#%% Just some test - care the directories

# Load the list of all videos
vid_list = pd.read_csv('F:/vot2017/list.txt', header = None)

# Name of a video can be accessed by e.g. vid_list[0][5]
print( vid_list[0][33])

 # Nr. of videos available
n = vid_list.shape[0]

test = VOT2017_dataset(csv_file= 'F:/vot2017/list.txt',
                       root_dir= 'F:/vot2017/')

# E.g. load the second video of the vid_list
sample = test[2]

# Simply draw a single video - here the idx refers to the image in the sequence
draw_gt(sample['Video'][0], sample['gt'][0])

# Test rescaling       
scale = Rescale((220,280))
transformed_sample = scale(sample)
draw_gt(transformed_sample['Video'][100], transformed_sample['gt'][100])

# Test the ToTensor - does not work on Nils Laptop     
tens = ToTensor()
tens(sample)

#%% Just for information - Find the smallest sized video

Vids = vid_list.shape[0]

Size = np.zeros((Vids, 2))

for i in range(Vids):
    im = Image.open(os.path.join('F:/vot2017/', 
                                     vid_list.iloc[i,0],
                                     '00000001.jpg'))
    Size[i,0] = im.size[0]
    Size[i,1] = im.size[1]

# Smallest size ist 320 x240

#%% define loss/reward functions; given the coordinates of all corners

def reward_v1(pred, gt):
    r = - np.mean(np.absolute(pred-gt)) - np.max(np.absolute(pred-gt))
    return r


# Calculate the reward given all the for corners x1,y1,x2,y2,x3,y3,x4,y4
def reward_v2(pred, gt):
    #reorder the coord in tuples for the polygon
    pred_re = [(pred[0],pred[1]),(pred[2],pred[3]), (pred[4],pred[5]),(pred[6],pred[7])]
    gt_re   = [(gt[0],gt[1]),(gt[2],gt[3]),(gt[4],gt[5]),(gt[6],gt[7])]
    
    pred_poly = Polygon(pred_re)
    gt_poly = Polygon(gt_re)
    # Reward == Intersection/total area
    r = pred_poly.intersection(gt_poly).area/(pred_poly.area + gt_poly.area - pred_poly.intersection(gt_poly).area)
    return r

#%% Test reward functions
    
test_1 = np.array((0,0,0,1,1,1,1,0))
test_2 = np.array((0.5,0,0.5,1,1.5,1,1.5,0))

print(reward_v1(test_1, test_2))
print(reward_v2(test_1, test_2))


#%%

class GaussianLayer(torch.autograd.Function):
    '''Implement custom gaussian layer here'''
    
    
    @staticmethod
    def forward(self, inp, sigma, N):
        '''
        We receive a Tensor input(take last 8 nr) from that we will draw outputs from a gaussian 
        distribution, centered around our inputs, with sigma as a covariance matrix
        N is the samples we draw
        '''
        cov = np.identity(8)*sigma # Covariance matrix
        output = np.random.multivariate_normal(inp[-8,:], cov, N) #sample form gaussian
        output = torch.from_numpy(output) # to tensor
        return output
    
    @staticmethod
    def backward(self, grad):
        '''
        Given grad as a tensor(8 values)
        '''
        self.grad = grad
        return grad
    
    
#%%
    
def calc_grad(pred_l, output, R_t, b_t, N, sigma):
      '''
      We receive pred_l(8xNxT) 
      also we receive our baseline b_t(T) and the cumulative rewards R_t(NxT)
      therefore we can compute the gradient as
      '''
      b_t.reshape((N,1)) # as is a vector we want column difference
      output.reshape((8,1)) # We want to have it as a column
      diff = R_t - b_t # is NxT
      ln_pi = np.zeros(pred_l.shape)
      # apperently have to use a for loop
      for i in range(N):
          ln_pi = pred_l-output/sigma**2 
      product = ln_pi*diff # 8xNxT
      grad_G = 1/N*np.sum(np.sum(product)) # Sum that up
      grad_G = torch.from_numpy(grad_G) # To torch
      return grad_G
      

#%%

#data reader  ----------------------------------------------------------------
class XXXXXDataset(Dataset):

    def __init__(self, split, transform=None, mode='train'):
        super(XXXXXXDataset, self).__init__()
        start = timer()

        self.split = split
        self.transform = transform
        self.mode = mode

        #read split
        ids = read_list_from_file(DATA_DIR + '/split/' + split, comment='#')

        #save
        self.ids = ids

        #print
        print('\ttime = %0.2f min'%((timer() - start) / 60))
        print('\tnum_ids = %d'%(len(self.ids)))
        print('')


    def __getitem__(self, index):
        id = self.ids[index]
        image_id = id.split('/')[-1]
        image = cv2.imread(DATA_DIR + '/image/' + id + '/images/' + image_id +'.png', cv2.IMREAD_COLOR)

        if self.mode in ['train']:
            multi_mask = np.load( DATA_DIR + '/image/' + id + '/multi_mask.npy')#.astype(int32)

            if self.transform is not None:
                return self.transform(image, multi_mask, index)
            else:
                return input, multi_mask, index

        if self.mode in ['test']:
            if self.transform is not None:
                return self.transform(image,index)
            else:
                return image, index

    def __len__(self):
        return len(self.ids)